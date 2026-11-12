import argparse
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

# quieter output from the Hugging Face libraries (set before they are imported)
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("HF_HUB_VERBOSITY", "error")

import tiktoken
from transformers import AutoTokenizer

HF_MODEL = (
    "Qwen/Qwen2.5-0.5B"  # open model, tokenizer files only (a few MB), no weights
)
DEFAULT_DOCUMENT = Path(__file__).resolve().parents[2] / "day-2" / "learning"

SAMPLES = {
    "English": "The quick brown fox jumps over the lazy dog.",
    "Hindi": "तेज़ भूरी लोमड़ी आलसी कुत्ते के ऊपर कूदती है।",
    "Hinglish": "Tez bhuri lomdi aalsi kutte ke upar kudti hai.",
    "Numbers": "1234567890 and 3.14159265 on 2026-11-05",
    "Code": "def add(a, b):\n    return a + b",
    "Typo": "helllo wrold",
}


@dataclass
class Tokenizer:
    name: str
    encode: Callable[[str], list[int]]
    piece: Callable[[int], str]

    def count(self, text: str) -> int:
        return len(self.encode(text))

    def pieces(self, text: str) -> list[str]:
        return [self.piece(token) for token in self.encode(text)]


def tiktoken_tokenizer(encoding_name: str) -> Tokenizer:
    encoding = tiktoken.get_encoding(encoding_name)
    return Tokenizer(
        name=f"tiktoken {encoding_name}",
        # disallowed_special=(): treat text like "<|endoftext|>" as normal text instead of raising an error
        encode=lambda text: encoding.encode(text, disallowed_special=()),
        piece=lambda token: encoding.decode_single_token_bytes(token).decode(
            "utf-8", errors="replace"
        ),
    )


def hf_tokenizer(model_name: str) -> Tokenizer:
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.model_max_length = (
        10**9
    )  # only counting, so silence the "longer than the maximum" warning
    return Tokenizer(
        name=f"HF {model_name}",
        encode=lambda text: tokenizer.encode(text, add_special_tokens=False),
        piece=lambda token: str(tokenizer.decode([token])),
    )


def read_documents(paths: list[Path]) -> tuple[str, list[Path]]:
    """Join the given files (or every .md/.txt file inside a given folder) into one long text."""
    files: list[Path] = []
    for path in paths:
        files.extend(
            sorted(p for p in path.rglob("*") if p.suffix in {".md", ".txt"})
            if path.is_dir()
            else [path]
        )
    text = "\n\n".join(file.read_text(encoding="utf-8") for file in files)
    return text, files


def print_table(rows: list[list[str]], header: list[str]) -> None:
    widths = [max(len(str(r[i])) for r in [header, *rows]) for i in range(len(header))]
    for row in [header, *rows]:
        print(
            "  ".join(
                str(cell).ljust(width) if i == 0 else str(cell).rjust(width)
                for i, (cell, width) in enumerate(zip(row, widths, strict=True))
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Count tokens with several tokenizers."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="files or folders to count (default: the Day 2 notes)",
    )
    args = parser.parse_args()

    tokenizers = [
        tiktoken_tokenizer("cl100k_base"),
        tiktoken_tokenizer("o200k_base"),
        hf_tokenizer(HF_MODEL),
    ]
    names = [t.name for t in tokenizers]

    print("1. Short samples: the same meaning costs a different number of tokens\n")
    rows = [
        [label, str(len(text)), *[str(t.count(text)) for t in tokenizers]]
        for label, text in SAMPLES.items()
    ]
    print_table(rows, ["text", "chars", *names])

    print("\n2. How one sentence is split (tiktoken o200k_base)\n")
    print(tokenizers[1].pieces(SAMPLES["English"]))
    print(tokenizers[1].pieces("unbelievably strawberry 2026"))

    print("\n3. A long document\n")
    text, files = read_documents(args.paths or [DEFAULT_DOCUMENT])
    words = len(text.split())
    print(f"{len(files)} file(s), {len(text):,} characters, {words:,} words")
    rows = []
    for tokenizer in tokenizers:
        count = tokenizer.count(text)
        rows.append(
            [
                tokenizer.name,
                f"{count:,}",
                f"{len(text) / count:.2f}",
                f"{count / words:.2f}",
            ]
        )
    print_table(rows, ["tokenizer", "tokens", "chars/token", "tokens/word"])


if __name__ == "__main__":
    main()
