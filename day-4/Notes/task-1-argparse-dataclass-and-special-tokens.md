# `argparse`, `@dataclass`, `encode` / `pieces` and special tokens

Question: what is `argparse`, what does the comment `# open model, tokenizer files only (a few MB), no weights` mean, what is `@dataclass`, and what are `encode`, `pieces`, `allowed_special` and `disallowed_special`?

Code: `day-4/tasks/task1_token_counts.py`.

## 1. What is `argparse`?
`argparse` is a module in Python's standard library for **reading command-line arguments**, like `commander` or `yargs` in Node.

```python
parser = argparse.ArgumentParser(description="Count tokens with several tokenizers.")
parser.add_argument("paths", nargs="*", type=Path, help="files or folders to count (default: the Day 2 notes)")
args = parser.parse_args()
```
| Part | Meaning |
|---|---|
| `ArgumentParser(description=...)` | Creates the parser; the description appears in `--help` |
| `add_argument("paths", ...)` | Declares an argument called `paths` |
| `nargs="*"` | Zero or more values |
| `type=Path` | Converts each value to a `Path` object |
| `help=...` | Text shown in `--help` |
| `parse_args()` | Reads what was typed and returns an object; `args.paths` is a list of `Path` |

```bash
uv run python tasks/task1_token_counts.py                  # args.paths is []  → use the default folder
uv run python tasks/task1_token_counts.py data/my_text.md       # args.paths is [Path("my_text.md")]
uv run python tasks/task1_token_counts.py a.md b.md        # two files
```
`--help` comes for free:
```
usage: task1_token_counts.py [-h] [paths ...]

positional arguments:
  paths       files or folders to count (default: the Day 2 notes)
```
It reports a clear error for bad input too. (`typer`, used in docstore, is a nicer layer on top of the same idea.)

## 2. The comment on `HF_MODEL`
```python
HF_MODEL = "Qwen/Qwen2.5-0.5B"  # open model, tokenizer files only (a few MB), no weights
```
- **open model:** the maker published it for anyone to download, with no login or approval. Some models on Hugging Face are "gated" and need terms accepted first.
- **tokenizer files only (a few MB):** `AutoTokenizer.from_pretrained(...)` downloads just the small files that define how text is split into tokens (`tokenizer.json`, the vocabulary and so on), not the whole model.
- **no weights:** the weights are the billions of numbers that make the model work. They are the huge part, often gigabytes. Counting tokens does not need them, so they are never downloaded.

## 3. What is `@dataclass`?
A decorator that **writes the boring class code for me**:
```python
@dataclass
class Tokenizer:
    name: str
    encode: Callable[[str], list[int]]
    piece: Callable[[int], str]
```
It automatically adds:
- an `__init__` that takes `name`, `encode` and `piece`,
- a readable `__repr__`,
- an `__eq__`.

So `Tokenizer(name="x", encode=..., piece=...)` works without writing the `__init__` and assigning each field. It is like a TypeScript interface that is also a real class. In this script it is a small bundle of three things for one tokenizer, so `tiktoken` and Hugging Face can be used the same way. (More: `day-1/Notes/task-3-docstore-walkthrough.md`.)

## 4. `encode`, `pieces`, `allowed_special`, `disallowed_special`

### `encode`
Turns text into **token ids**, a list of integers. The model sees these numbers, not letters.
```python
enc.encode("नमस्ते")      # [998, 1637, 14681, 628]
```
`len()` of that list is the token count.

### `pieces` and `piece`
They turn token ids back into **pieces of text**, so I can see where the text was cut.
```python
['The', ' quick', ' brown', ' fox', ...]
```
- `piece(token)` converts **one** token id to text.
- `pieces(text)` does it for every id in the text.

### Why `.decode("utf-8", errors="replace")`
`decode_single_token_bytes` gives the **bytes** of one token, and a token can end in the middle of a character. Measured with the emoji 🙂 and `cl100k_base`:
- its two tokens have the bytes `b'\xf0\x9f'` and `b'\x99\x82'`,
- neither is valid UTF-8 on its own,
- `errors="replace"` shows a `�` for each instead of crashing,
- decoded together, the two tokens give 🙂 back.

### Special tokens
**Special tokens** are reserved tokens that control the model. One is `<|endoftext|>`, meaning "the text ends here". If ordinary text contains that exact string, `tiktoken` must decide what to do. Tested with `Hello <|endoftext|> world` and `o200k_base`:

**Default** (no setting)
- It raises an error: `ValueError: Encountered text corresponding to disallowed special token '<|endoftext|>'`.
- Reason: the text looks like a control token, which could be a mistake or an attack.

**`disallowed_special=()`**
- Nothing is forbidden, so the string is treated as **normal text**.
- Result: 9 tokens, `Hello`, ` <`, `|`, `end`, `of`, `text`, `|`, `>`, ` world`.

**`allowed_special="all"`**
- The string is treated as the **real special token**.
- Result: 4 tokens, `Hello`, ` `, `<|endoftext|>`, ` world`. The special token is one id (199999).

What the names mean:
- `allowed_special`: special tokens that are allowed to become real special tokens.
- `disallowed_special`: special tokens that must **not** appear in the text; if one does, `tiktoken` raises the error.

The script passes `disallowed_special=()`: when counting tokens in any file, a stray `<|endoftext|>` is counted as text and does not crash the script.

(On the Hugging Face side the similar idea is `add_special_tokens=False`: count only my text, without extra start or end tokens.)

## Common mistakes
| Mistake | What happens |
|---|---|
| Forgetting `type=Path` in `add_argument` | `args.paths` holds plain strings |
| Counting text that contains a special-token string with the default settings | `ValueError` |
| Using `allowed_special="all"` on user-supplied text | A user can inject control tokens |
| Decoding a single token's bytes without `errors="replace"` | `UnicodeDecodeError` on partial characters |
| Expecting the Hugging Face call to download the whole model | Only the tokenizer files are fetched |

## Quick check
- What does `parser.parse_args()` return, and what is `nargs="*"`?
- Why is no model weight file downloaded for this task?
- What three things does `@dataclass` generate?
- What is the difference between `encode` and `piece`?
- What happens with the text `<|endoftext|>` under the default, `disallowed_special=()` and `allowed_special="all"`?
