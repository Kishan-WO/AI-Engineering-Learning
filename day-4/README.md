# Day 4: LLM fundamentals

Everything here belongs to one task or to the learning part. Run every command from this folder (`day-4`).

## Layout
```
day-4/
  README.md            this index
  .env                 private settings (API key); not committed
  .env.example         template for .env
  pyproject.toml       uv project (packages)
  learning/            the 8 concept notes (what an LLM is, tokens, context window ...)
  tasks/               the code, one file per task, plus the shared client
  data/                input files for the tasks
  results/             saved output of the tasks
  Notes/               one note per task, named task-N-...
```

## Learning notes (`learning/`)
| Note | Topic |
|---|---|
| `1.how-an-llm-works.md` | Next-token prediction, training stages, transformers, reasoning models |
| `2.tokens.md` | Tokens, BPE, tokenisers, Hindi cost, pricing |
| `3.context-window.md` | Context window, stateless model, why a chatbot forgets |
| `4.inference-vs-training.md` | Frozen weights, knowledge cutoff |
| `5.sampling-parameters.md` | temperature, top_p, top_k, penalties, seeds |
| `6.model-landscape.md` | Closed and open models, sizes, latency, leaderboards |
| `7.hallucination.md` | Why models invent facts and how to reduce it |
| `8.local-models.md` | Ollama, quantisation, the OpenAI-compatible endpoint |

## Tasks
| Task | What | Code (`tasks/`) | Input and output | Note (`Notes/`) |
|---|---|---|---|---|
| **1** | Count tokens with `tiktoken` and a Hugging Face tokenizer | `task1_token_counts.py` | `data/my_text.md` | `task-1-token-counting.md`, `task-1-argparse-dataclass-and-special-tokens.md` |
| **2** | English vs Hindi vs Hinglish: tokens and cost for 1M messages | `task2_language_cost.py` | `data/my_text.md` | `task-2-language-token-cost.md` |
| **3** | Same prompt at temperature 0, 0.7, 1.4, five times each | `task3_temperature_variance.py` | `results/task3_results.json`, `results/task3_results_factual.json` | `task-3-temperature-variance.md` |
| **4** | One open model locally and a hosted model, same code | `task4_same_code.py`, `task4_show_raw_response.py`, `llm_client.py` (shared) | `.env` | `task-4-same-code-local-and-hosted.md`, `task-4-profiles-client-and-http-shape.md` |
| **5** | Terminal chat with history; cap it at 4 messages to see it forget | `task5_terminal_chat.py` | | `task-5-terminal-chat-why-a-chatbot-forgets.md` |
| **6** | Time-to-first-token and total latency, small vs large model | `task6_latency.py` | `results/task6_latency.json` | `task-6-latency-small-vs-large.md` |
| **7** | Ask for three citations on a niche topic and verify them | `task7_citations.py` | `results/task7_citations.json` | `task-7-citations-hallucination-test.md` |

`tasks/llm_client.py` is shared: it holds the two profiles (`local`, `gemini`) and `chat()` / `chat_messages()`. Tasks 4 and 5 (and later 6 and 7) use it.

## How to run each task
```bash
uv run python tasks/task1_token_counts.py
uv run python tasks/task1_token_counts.py data/my_text.md

uv run python tasks/task2_language_cost.py

uv run python tasks/task3_temperature_variance.py
uv run python tasks/task3_temperature_variance.py --prompt "Name one fruit. Reply with one word." --results results/task3_results_fruit.json

uv run python tasks/task4_same_code.py
uv run python tasks/task4_same_code.py --list-models gemini
uv run python tasks/task4_show_raw_response.py          # the raw request and the full response

uv run python tasks/task5_terminal_chat.py --cap 4
uv run python tasks/task5_terminal_chat.py --demo --profile gemini

uv run python tasks/task6_latency.py
uv run python tasks/task6_latency.py --models local gemini gemini:gemini-3.6-flash --runs 5

uv run python tasks/task7_citations.py              # about 4 minutes: 3 models, 2 prompts, lookups in Crossref and OpenAlex
```

## Setup
- `uv sync` installs the packages.
- Local model: Ollama running with `gemma3:270m` (`ollama list`).
- Hosted model: put the Gemini key in `.env` (`GEMINI_API_KEY=`) and the model name in `GEMINI_MODEL=`. `.env` is git-ignored; never paste the key anywhere else.
