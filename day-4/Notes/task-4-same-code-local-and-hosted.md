# Task 4: one open model run locally, called with the same code as a hosted model

Task: run one open model locally with Ollama or LM Studio, and call it through the OpenAI-compatible endpoint with the same code used for a hosted model.

Files:
- `day-4/tasks/llm_client.py`: the shared client code and the two profiles.
- `day-4/tasks/task4_same_code.py`: sends one prompt to every configured profile and prints the result.
- `day-4/.env` (private, not committed) and `day-4/.env.example` (the template).

```bash
uv run python tasks/task4_same_code.py                       # both profiles
uv run python tasks/task4_same_code.py --profile local       # only the local model
uv run python tasks/task4_same_code.py --list-models gemini  # which model names the key can use
uv run python tasks/task4_same_code.py --prompt "Your own question"
```

## 1. The idea
Ollama and Gemini both offer the same HTTP shape as the OpenAI chat API (`POST .../chat/completions`). So one client class, `openai.OpenAI`, talks to both. Only three values differ:

| Setting | Local (Ollama) | Hosted (Gemini) |
|---|---|---|
| `base_url` | `http://localhost:11434/v1` | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `api_key` | any text (`"ollama"`; Ollama ignores it) | my real key, from `.env` |
| `model` | `gemma3:270m` | `gemini-3.1-flash-lite` |

Everything else, including the function that sends the message, is **identical**:
```python
client, model = make_client(profile_name)       # the only line that depends on the profile
reply = chat(client, model, prompt, temperature=0.0, max_tokens=200)
```

## 2. How the code is organised
- **`PROFILES`** (a dictionary of small frozen dataclasses) holds the base URL and the names of the environment variables for each profile.
- **`make_openai_client(profile)`** builds the client; it needs the key but not the model name.
- **`model_name(profile)`** reads the model name from `.env` and raises `MissingConfigError` if it is empty.
- **`make_client(profile)`** calls both.
- **`chat(client, model, prompt, ...)`** sends one user message and returns a `Reply` with the text, prompt tokens, completion tokens and seconds.
- A missing key or model does not crash the run: that profile prints `skipped: ...` and the others continue.

### A bug I fixed on the way
My first `--list-models` used a hack that set a dummy model name. It failed because `python-dotenv` loads `GEMINI_MODEL=` (empty) as an empty string, so the variable *exists* and `os.environ.setdefault` does nothing. The fix was to split the client building from the model lookup, so listing models never needs a model name.

## 3. Result (same prompt, temperature 0)
Prompt: "In two short sentences, explain what a token is in a language model."

| | Hosted: `gemini-3.1-flash-lite` | Local: `gemma3:270m` |
|---|---|---|
| Answer | A fundamental unit of text (a word, part of a word or a character) processed as a single numerical value; building blocks that let the model break down and interpret language. Two clear sentences | One sentence: "a unit of data in a language model, representing a specific word, phrase, or concept." Shorter, vaguer, and not two sentences |
| Prompt tokens | 16 | 24 |
| Completion tokens | 53 | 24 |
| Time | 2.42 s | 5.62 s |

What the comparison shows:
- **Quality:** the hosted model followed the "two sentences" instruction and was more precise. The 270M model is a tiny test model.
- **Token counts are not portable.** The same text counted as 16 prompt tokens on Gemini and 24 on Ollama. Different tokenisers, and the local count also includes the chat template tokens that wrap the message.
- **Speed:** the hosted call was faster here, although the model is far bigger. The local model runs on this machine's CPU (the GPU is too small), and the first call after a pause also loads the model into memory.
- **Cost:** the local call costs nothing; the hosted call has a price (below).

## 4. Cost of that one hosted call
`gemini-3.1-flash-lite` paid tier: 0.25 USD per million input tokens and 1.50 per million output tokens (prices read from Google's page on 12 Nov 2026; check again before relying on them).

```
16 × 0.25 / 1,000,000  =  0.000004
53 × 1.50 / 1,000,000  =  0.0000795
total                  ≈  0.00008 USD
```
On the free tier the call is free, but the free tier allows Google to use the prompts to improve its products, so keep test prompts non-sensitive.

## 5. Safety habits
- The key lives only in `day-4/.env`, which is listed in `.gitignore`; only `.env.example` (with an empty key) is committed.
- The script never prints the key.
- A spend limit or budget alert is set in Google's console before using a paid project.

## 6. Switching providers
To use another OpenAI-compatible provider, add a `Profile` with its base URL, the name of its key variable and the name of its model variable; nothing else in the calling code changes.

## Quick check
- Which three values change between the local and the hosted call?
- Why can one `OpenAI` client class talk to both?
- Why did the same prompt count as 16 tokens on one side and 24 on the other?
- Why does a missing key skip one profile instead of crashing the run?
- Why was the `setdefault` workaround for listing models wrong?
