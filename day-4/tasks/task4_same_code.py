"""Day 4, task 4: the same code calls a local open model and a hosted model.

uv run python tasks/task4_same_code.py                       # both profiles that are configured
uv run python tasks/task4_same_code.py --profile local       # only the local model
uv run python tasks/task4_same_code.py --list-models gemini  # which model names a profile offers
"""

import argparse

from llm_client import (
    PROFILES,
    MissingConfigError,
    chat,
    make_client,
    make_openai_client,
)

DEFAULT_PROMPT = "In two short sentences, explain what a token is in a language model."


def list_models(profile_name: str) -> None:
    """Print the model names a profile offers (needed to fill in the model name in .env)."""
    try:
        client = make_openai_client(profile_name)
    except MissingConfigError as error:
        raise SystemExit(f"[{profile_name}] {error}") from error
    names = sorted(model.id for model in client.models.list())
    print(f"{len(names)} model(s) for profile {profile_name!r}:")
    for name in names:
        print("  ", name)


def run(profile_name: str, prompt: str, max_tokens: int) -> None:
    try:
        client, model = make_client(profile_name)
    except MissingConfigError as error:
        print(f"[{profile_name}] skipped: {error}\n")
        return
    reply = chat(client, model, prompt, temperature=0.0, max_tokens=max_tokens)
    print(f"[{profile_name}] model {model}")
    print(f"  answer:  {reply.text}")
    print(
        f"  tokens:  {reply.prompt_tokens} in, {reply.completion_tokens} out   time: {reply.seconds:.2f}s\n"
    )
    print(reply)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Call a local and a hosted model with the same code."
    )
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument(
        "--profile", choices=sorted(PROFILES), help="only this profile (default: all)"
    )
    parser.add_argument("--max-tokens", type=int, default=200)
    parser.add_argument(
        "--list-models",
        choices=sorted(PROFILES),
        metavar="PROFILE",
        help="list model names and exit",
    )
    args = parser.parse_args()

    if args.list_models:
        list_models(args.list_models)
        return

    print(f"Prompt: {args.prompt!r}\n")
    for name in [args.profile] if args.profile else sorted(PROFILES):
        run(name, args.prompt, args.max_tokens)


if __name__ == "__main__":
    main()
