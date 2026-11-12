import argparse
import json
import statistics
import time
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

from openai import OpenAI

BASE_URL = "http://localhost:11434/v1"
MODEL = "gemma3:270m"
TEMPERATURES = (0.0, 0.7, 1.4)
DEFAULT_PROMPT = (
    "Suggest a name for a new coffee shop in Ahmedabad. Reply with only the name."
)
RESULTS_FILE = Path(__file__).parent.parent / "results" / "task3_results.json"


@dataclass
class Answer:
    temperature: float
    run: int
    text: str
    completion_tokens: int
    seconds: float


def ask(
    client: OpenAI, prompt: str, temperature: float, max_tokens: int
) -> tuple[str, int, float]:
    start = time.perf_counter()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    seconds = time.perf_counter() - start
    text = (response.choices[0].message.content or "").strip()
    tokens = response.usage.completion_tokens if response.usage else 0
    return text, tokens, seconds


def similarity(texts: list[str]) -> float:
    """Average similarity (0 to 1) over all pairs of answers. 1.0 means every answer is identical."""
    pairs = list(combinations(texts, 2))
    if not pairs:
        return 1.0
    return statistics.mean(SequenceMatcher(None, a, b).ratio() for a, b in pairs)


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
        description="Compare answer variance at different temperatures."
    )
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--runs", type=int, default=5, help="calls per temperature")
    parser.add_argument("--max-tokens", type=int, default=30)
    parser.add_argument(
        "--results",
        type=Path,
        default=RESULTS_FILE,
        help="where to save the raw answers",
    )
    args = parser.parse_args()

    client = OpenAI(
        base_url=BASE_URL, api_key="ollama"
    )  # Ollama ignores the key, the client needs some text

    print(
        f"Model: {MODEL}   Prompt: {args.prompt!r}   {args.runs} calls per temperature\n"
    )
    ask(
        client, "Say hi.", 0.0, 5
    )  # warm-up: the first call also loads the model into memory

    answers: list[Answer] = []
    for temperature in TEMPERATURES:
        print(f"--- temperature {temperature}")
        for run in range(1, args.runs + 1):
            text, tokens, seconds = ask(
                client, args.prompt, temperature, args.max_tokens
            )
            answers.append(Answer(temperature, run, text, tokens, seconds))
            print(f"  {run}. {text!r}")

    print("\nSummary\n")
    rows = []
    for temperature in TEMPERATURES:
        group = [a for a in answers if a.temperature == temperature]
        texts = [a.text for a in group]
        lengths = [a.completion_tokens for a in group]
        rows.append(
            [
                str(temperature),
                f"{len(set(texts))} of {len(texts)}",
                f"{similarity(texts):.2f}",
                f"{statistics.mean(lengths):.1f}",
                f"{statistics.pstdev(lengths):.1f}",
                f"{statistics.mean(a.seconds for a in group):.2f}",
            ]
        )
    print_table(
        rows,
        [
            "temperature",
            "distinct answers",
            "avg similarity",
            "avg tokens",
            "token stdev",
            "avg seconds",
        ],
    )

    args.results.parent.mkdir(parents=True, exist_ok=True)
    args.results.write_text(
        json.dumps(
            {
                "model": MODEL,
                "prompt": args.prompt,
                "answers": [asdict(a) for a in answers],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nRaw answers saved to {args.results.name}")


if __name__ == "__main__":
    main()
