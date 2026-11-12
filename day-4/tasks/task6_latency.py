"""Day 4, task 6: measure time-to-first-token (TTFT) and total latency for a small and a large model.

Each model gets the same prompt, with streaming switched on, so the first piece of text can be timed.

    uv run python tasks/task6_latency.py
    uv run python tasks/task6_latency.py --models local gemini gemini:gemini-2.5-pro --runs 5

A model is written as `profile` (uses the model name from .env) or `profile:model-name`.
"""

import argparse
import json
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from openai import APIError, OpenAI

from llm_client import PROFILES, MissingConfigError, make_openai_client, model_name

DEFAULT_PROMPT = (
    "Explain in about 100 words what an API rate limit is and why services use it."
)
DEFAULT_MODELS = ["local", "gemini", "gemini:gemini-2.5-pro"]
RESULTS_FILE = Path(__file__).parent.parent / "results" / "task6_latency.json"


@dataclass
class Run:
    ttft: float  # seconds until the first piece of text arrived
    total: float  # seconds until the stream ended
    completion_tokens: int
    characters: int


@dataclass
class Example:
    """One streamed chunk, as the server sent it, so I can see what a stream really contains."""

    first_text_chunk: dict[str, Any]
    last_chunk: dict[str, Any]


def parse_spec(spec: str) -> tuple[str, str]:
    """'gemini:gemini-2.5-pro' -> ('gemini', 'gemini-2.5-pro');  'local' -> ('local', <model from .env>)."""
    profile, _, explicit_model = spec.partition(":")
    if profile not in PROFILES:
        raise SystemExit(f"unknown profile {profile!r}; choose from {sorted(PROFILES)}")
    return profile, explicit_model or model_name(profile)


def measure(
    client: OpenAI, model: str, prompt: str, max_tokens: int
) -> tuple[Run, Example]:
    start = time.perf_counter()
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=max_tokens,
        stream=True,
        stream_options={
            "include_usage": True
        },  # asks for the token counts in a final chunk
    )
    ttft: float | None = None
    characters = 0
    tokens = 0
    first_text_chunk: dict[str, Any] = {}
    last_chunk: dict[str, Any] = {}
    for chunk in stream:
        last_chunk = chunk.model_dump(exclude_none=True)
        if chunk.usage:
            tokens = chunk.usage.completion_tokens
        text = chunk.choices[0].delta.content if chunk.choices else None
        if text:
            characters += len(text)
            if ttft is None:
                ttft = time.perf_counter() - start
                first_text_chunk = chunk.model_dump(exclude_none=True)
    total = time.perf_counter() - start
    run = Run(
        ttft=ttft if ttft is not None else total,
        total=total,
        completion_tokens=tokens,
        characters=characters,
    )
    return run, Example(first_text_chunk, last_chunk)


def print_table(rows: list[list[str]], header: list[str]) -> None:
    widths = [max(len(row[i]) for row in [header, *rows]) for i in range(len(header))]
    for row in [header, *rows]:
        print(
            "  ".join(
                cell.ljust(w) if i == 0 else cell.rjust(w)
                for i, (cell, w) in enumerate(zip(row, widths, strict=True))
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure TTFT and total latency for several models."
    )
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS, metavar="SPEC")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--runs", type=int, default=3, help="measured runs per model")
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1500,
        help="a thinking model also spends these on its thinking",
    )
    args = parser.parse_args()

    print(f"Prompt: {args.prompt!r}   {args.runs} measured runs per model, streaming\n")
    summary: list[list[str]] = []
    saved: dict[str, Any] = {"prompt": args.prompt, "models": {}}
    examples: dict[str, Example] = {}

    for spec in args.models:
        profile, model = parse_spec(spec)
        label = f"{profile}:{model}"
        try:
            client = make_openai_client(profile)
            measure(
                client, model, "Say hi.", 50
            )  # warm-up: loads a local model, opens the connection
            runs: list[Run] = []
            for number in range(1, args.runs + 1):
                run, example = measure(client, model, args.prompt, args.max_tokens)
                runs.append(run)
                examples.setdefault(label, example)
                print(
                    f"  {label:<34} run {number}: TTFT {run.ttft:6.2f}s   total {run.total:6.2f}s   {run.completion_tokens} tokens"
                )
        except MissingConfigError as error:
            print(f"  {label}: skipped ({error})")
            continue
        except APIError as error:
            print(f"  {label}: stopped by the API: {error}")
            continue

        speeds = [
            (r.completion_tokens / (r.total - r.ttft)) if r.total > r.ttft else 0.0
            for r in runs
        ]
        summary.append(
            [
                label,
                f"{statistics.median(r.ttft for r in runs):.2f}",
                f"{statistics.median(r.total for r in runs):.2f}",
                f"{statistics.median(r.completion_tokens for r in runs):.0f}",
                f"{statistics.median(speeds):.0f}",
            ]
        )
        saved["models"][label] = [asdict(r) for r in runs]

    print("\nMedian of the runs\n")
    print_table(
        summary,
        ["model", "TTFT (s)", "total (s)", "output tokens", "tokens/s after first"],
    )

    for label, example in examples.items():
        print(f"\n--- what the stream looks like for {label}")
        print("first chunk that carried text:")
        print(json.dumps(example.first_text_chunk, indent=2, ensure_ascii=False)[:700])
        print("last chunk:")
        print(json.dumps(example.last_chunk, indent=2, ensure_ascii=False)[:700])

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_FILE.write_text(
        json.dumps(saved, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nRaw timings saved to results/{RESULTS_FILE.name}")


if __name__ == "__main__":
    main()
