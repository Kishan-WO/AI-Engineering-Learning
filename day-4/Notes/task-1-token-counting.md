# Task 1: count tokens with `tiktoken` and a Hugging Face tokenizer

Task: run `tiktoken` and one other model's tokenizer on my own text, and count the tokens in a long document.

Script: `day-4/tasks/task1_token_counts.py`. Run from `day-4`:
```bash
uv run python tasks/task1_token_counts.py                  # short samples + the Day 2 notes as the long document
uv run python tasks/task1_token_counts.py data/my_text.md       # my own file(s)
uv run python tasks/task1_token_counts.py some_folder      # every .md / .txt file inside a folder
```

## 1. What I used
| Tokenizer | Library | Notes |
|---|---|---|
| `cl100k_base` | `tiktoken` | The older OpenAI encoding |
| `o200k_base` | `tiktoken` | The newer OpenAI encoding, larger vocabulary |
| `Qwen/Qwen2.5-0.5B` | `transformers` (`AutoTokenizer`) | An open model. Only the tokenizer files are downloaded (a few MB), not the model weights |

Setup: a `day-4` uv project (`uv add tiktoken transformers`). The Hugging Face files are cached in `~/.cache/huggingface`, so later runs also work offline.

## 2. Short samples (measured)
| Text | Characters | cl100k | o200k | Qwen2.5 |
|---|---|---|---|---|
| English sentence | 44 | 10 | 10 | 10 |
| Hindi (same meaning) | 45 | **49** | **20** | **46** |
| Hinglish (Hindi in Roman letters) | 46 | 20 | 18 | 20 |
| Numbers (`1234567890 and 3.14159265 on 2026-11-05`) | 39 | 19 | 19 | **34** |
| Code (`def add(a, b): ...`) | 31 | 11 | 11 | 11 |
| Typos (`helllo wrold`) | 12 | 5 | 5 | 5 |

## 3. A long document (measured)
The long document is the 12 numbered Day 2 notes joined together: **109,356 characters, 16,901 words**.

| Tokenizer | Tokens | Chars per token | Tokens per word |
|---|---|---|---|
| tiktoken `cl100k_base` | 28,738 | 3.81 | 1.70 |
| tiktoken `o200k_base` | 28,808 | 3.80 | 1.70 |
| HF `Qwen/Qwen2.5-0.5B` | 28,976 | 3.77 | 1.71 |

Other texts: the 50 sample documents together (20,337 characters) are 4,330 to 4,408 tokens (about 4.6 characters per token); one 404-character file is 90 to 92 tokens.

## 4. What I found
- **English prose is about 4 characters per token** (4.4 to 4.7 on the sample documents). The long document came out lower, about 3.8, because it is Markdown full of code, tables and symbols.
- **For English the three tokenizers agree within about 1%** (28,738 to 28,976 on the long document). Counts only drift apart on other kinds of text.
- **Hindi is the big difference.** The same sentence is 49 tokens with `cl100k` and 20 with `o200k`, while Qwen needs 46. A newer tokeniser can cut the cost by more than half, an older one can cost almost 5 times the English count.
- **Numbers depend on the tokeniser.** `tiktoken` groups digits in threes (`202` + `6`); Qwen splits every digit, so the numbers sample was 34 tokens against 19.
- **A leading space is part of the token.** `" strawberry"` (with a space) is one token, but `"strawberry"` at the start of a text is three (`st` | `raw` | `berry`).
- **Token counts are not portable** between model families, which is why billing and limits must use the provider's own tokeniser.

## 5. How the script works
- A small `Tokenizer` dataclass holds three things: a name, an `encode` function and a `piece` function, so `tiktoken` and Hugging Face are used the same way.
- `encode(text, disallowed_special=())` stops `tiktoken` raising an error when the text contains something like `<|endoftext|>`.
- `add_special_tokens=False` on the Hugging Face side counts only the text, without extra start or end tokens.
- `model_max_length` is raised so the library does not warn about long documents; this task only counts.
- Checks: `ruff` and `mypy --strict` pass on the script.

## Quick check
- Why are the three English counts almost equal, but the Hindi counts so different?
- Why is the long document at 3.8 characters per token and not 4?
- How does Qwen tokenise numbers differently from `tiktoken`?
- Why must I count with the provider's own tokeniser?
