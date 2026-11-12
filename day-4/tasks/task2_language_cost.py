import argparse
import re
from pathlib import Path

from task1_token_counts import HF_MODEL, Tokenizer, hf_tokenizer, tiktoken_tokenizer

DEFAULT_FILE = Path(__file__).parent.parent / "data" / "my_text.md"
LANGUAGES = ("English", "Hindi", "Hinglish")
MESSAGES_PER_RUN = 1_000_000


def read_messages(path: Path) -> dict[str, str]:
    """Read the paragraphs under the '### English', '### Hindi' and '### Hinglish' headings."""
    text = path.read_text(encoding="utf-8")
    messages: dict[str, str] = {}
    for language in LANGUAGES:
        match = re.search(
            rf"^### {language}\s*\n(.+?)(?=\n#|\Z)",
            text,
            flags=re.DOTALL | re.MULTILINE,
        )
        if match is None:
            raise SystemExit(f"{path} has no '### {language}' section")
        messages[language] = match.group(1).strip()
    return messages


def cost_for_messages(
    tokens: int, input_price: float, output_price: float, reply_ratio: float, count: int
) -> float:
    """Cost of `count` messages of `tokens` tokens each.

    Each message is input; the reply is assumed to be `reply_ratio` times as long, in the same language.
    Prices are per million tokens.
    """
    input_tokens = tokens * count
    output_tokens = tokens * reply_ratio * count
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000


def print_table(rows: list[list[str]], header: list[str]) -> None:
    widths = [max(len(row[i]) for row in [header, *rows]) for i in range(len(header))]
    for row in [header, *rows]:
        print(
            "  ".join(
                cell.ljust(w) if i == 0 else cell.rjust(w)
                for i, (cell, w) in enumerate(zip(row, widths, strict=True))
            )
        )


def report(
    tokenizer: Tokenizer, messages: dict[str, str], args: argparse.Namespace
) -> None:
    print(f"\n=== {tokenizer.name}")
    counts = {language: tokenizer.count(text) for language, text in messages.items()}
    costs = {
        language: cost_for_messages(
            count,
            args.input_price,
            args.output_price,
            args.reply_ratio,
            MESSAGES_PER_RUN,
        )
        for language, count in counts.items()
    }
    base_tokens, base_cost = counts["English"], costs["English"]
    rows = []
    for language, text in messages.items():
        rows.append(
            [
                language,
                str(len(text)),
                str(counts[language]),
                f"{counts[language] / base_tokens:.2f}x",
                f"{costs[language]:,.0f}",
                f"{costs[language] - base_cost:+,.0f}",
            ]
        )
    print_table(
        rows,
        [
            "language",
            "chars",
            "tokens",
            "vs English",
            "USD for 1M messages",
            "difference vs English",
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare token counts and cost for English, Hindi and Hinglish."
    )
    parser.add_argument(
        "file",
        nargs="?",
        type=Path,
        default=DEFAULT_FILE,
        help="a markdown file with ### English / ### Hindi / ### Hinglish sections",
    )
    parser.add_argument(
        "--input-price",
        type=float,
        default=1.0,
        help="USD per million input tokens (example value)",
    )
    parser.add_argument(
        "--output-price",
        type=float,
        default=4.0,
        help="USD per million output tokens (example value)",
    )
    parser.add_argument(
        "--reply-ratio",
        type=float,
        default=1.0,
        help="reply length as a multiple of the message length",
    )
    args = parser.parse_args()

    messages = read_messages(args.file)
    print(
        f"Messages from {args.file.name}; 1 message = 1 paragraph; {MESSAGES_PER_RUN:,} messages"
    )
    print(
        f"Example prices: input {args.input_price}/M, output {args.output_price}/M USD; reply = {args.reply_ratio}x the message"
    )

    for tokenizer in [
        tiktoken_tokenizer("cl100k_base"),
        tiktoken_tokenizer("o200k_base"),
        hf_tokenizer(HF_MODEL),
    ]:
        report(tokenizer, messages, args)

    print(
        "\nThe 'vs English' ratio does not depend on the price: the cost difference scales with the token ratio."
    )


if __name__ == "__main__":
    main()
