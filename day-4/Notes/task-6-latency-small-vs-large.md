# Task 6: time-to-first-token and total latency, small model vs large model

Task: measure TTFT and total latency for a small and a large model on the same prompt.

Script: `day-4/tasks/task6_latency.py`. Raw timings: `results/task6_latency.json`.
```bash
uv run python tasks/task6_latency.py
uv run python tasks/task6_latency.py --models local gemini gemini:gemini-3.6-flash --runs 5
```
A model is written as `profile` (the model name from `.env`) or `profile:model-name`.

## 1. How it is measured
- **Streaming** is switched on (`stream=True`), so the answer arrives in pieces and the first piece can be timed.
- **TTFT** = time from sending the request until the **first chunk that carries text**.
- **Total latency** = time until the stream ends.
- **Tokens per second after the first** = output tokens ÷ (total − TTFT).
- One warm-up call per model first (it loads a local model and opens the connection). Then 3 measured runs; the table shows the **median**.
- Prompt (the same for all): "Explain in about 100 words what an API rate limit is and why services use it." Temperature 0, `max_tokens` 1500 (a thinking model spends part of this on its thinking).

## 2. Result (median of 3 runs)
| Model | TTFT (s) | Total (s) | Output tokens | Tokens per second after the first |
|---|---|---|---|---|
| `gemma3:270m` (local, CPU, tiny) | 2.20 | 5.80 | 65 | 18 |
| `gemini-3.1-flash-lite` (hosted, small) | **1.28** | **2.26** | 118 | 122 |
| `gemini-3.6-flash` (hosted, large Flash tier) | 4.58 | 5.73 | 133 | 110 |
| `gemma-4-31b-it` (hosted, 31B open model) | 23.15 | 36.50 | 126 | 11 |

Every run:
| Model | Run 1 TTFT / total | Run 2 | Run 3 |
|---|---|---|---|
| `gemma3:270m` | 2.20 / 5.80 | 2.20 / 5.79 | 2.20 / 5.84 |
| `gemini-3.1-flash-lite` | 1.28 / 2.26 | 1.21 / 2.07 | 1.42 / 2.39 |
| `gemini-3.6-flash` | 35.57 / 36.79 | 4.58 / 5.73 | 4.27 / 4.97 |
| `gemma-4-31b-it` | 24.98 / 36.50 | 23.15 / 34.60 | 7.51 / 42.07 |

## 3. What I learned
- **The small model answers first**: TTFT 1.3 s against 4.6 s for the larger Flash, and 23 s for the 31B model.
- **After the first token, both Gemini models stream at a similar speed** (about 110 to 120 tokens per second). The big difference is *how long they wait before starting*, not how fast they write.
- **That wait is hidden thinking.** For `gemini-3.6-flash` the usage in the response was `completion_tokens=130` but `total_tokens=1152` with only 21 prompt tokens. So about **1,000 tokens were spent thinking** and are not in `completion_tokens`. The small model had no gap (139 total = 21 + 118). Thinking tokens cost time (TTFT) and are billed as output tokens, even though the answer is only about 104 words.
- **`completion_tokens` alone can understate the bill.** The honest count is `total_tokens − prompt_tokens`.
- **`gemma-4-31b-it` showed its thinking in the text** (`<thought> ... </thought>` before the answer): 1,851 characters for 126 counted tokens. It was also the slowest by far.
- **The local tiny model is steady but slow**: TTFT 2.2 s and 18 tokens per second on this CPU, with almost no spread between runs (2.19 to 2.28 s). Hosted models vary much more because of load.
- **Hosted timings are noisy.** The first run of `gemini-3.6-flash` took 35.6 s before the first token (a busy server), then 4.6 s and 4.3 s. Medians over several runs, at different times of day, are the honest figure; one run is not.
- **Small is not always "worse"** for a short task: here the small model gave a full answer in 2.3 s, a third of the time of the larger one for the same prompt. A larger model is worth the wait only when the task is hard.

## 4. What a stream looks like (real chunks)
Each piece of the answer is a small JSON object, `object: "chat.completion.chunk"`. The text is in `choices[0].delta.content`.

Local Ollama, the first chunk that carried text:
```json
{
  "choices": [{ "delta": { "content": "An", "role": "assistant" }, "index": 0 }],
  "created": 1794480419,
  "model": "gemma3:270m",
  "object": "chat.completion.chunk",
  "system_fingerprint": "fp_ollama"
}
```
and its last chunk (no choices; usage and Ollama's own timings):
```json
{
  "choices": [],
  "model": "gemma3:270m",
  "object": "chat.completion.chunk",
  "usage": { "completion_tokens": 65, "prompt_tokens": 29, "total_tokens": 94,
             "prompt_tokens_details": { "cached_tokens": 0 } },
  "timings": { "prompt_n": 29, "prompt_ms": 216, "prompt_per_second": 134.26,
               "predicted_n": 65, "predicted_ms": 3700, "predicted_per_second": 17.57 }
}
```
Ollama's `timings` block confirms my own measurement: 17.6 tokens per second against my 18.

Gemini, first text chunk:
```json
{
  "choices": [{ "delta": { "content": "An API", "role": "assistant" }, "index": 0 }],
  "model": "gemini-3.1-flash-lite",
  "object": "chat.completion.chunk",
  "usage": { "completion_tokens": 2, "prompt_tokens": 21, "total_tokens": 23 }
}
```
and its last chunk, which carries `finish_reason` and the totals:
```json
{
  "choices": [{ "delta": { "role": "assistant", "extra_content": { "google": { "thought_signature": "EnMKcQ... (long opaque string)" } } },
                "index": 0, "finish_reason": "stop" }],
  "model": "gemini-3.1-flash-lite",
  "usage": { "completion_tokens": 118, "prompt_tokens": 21, "total_tokens": 139 }
}
```
Notes: some chunks have no `choices` at all (the usage-only chunk), the first chunk may only carry the role, and Gemini repeats a running `usage` in the chunks. That is why the script only counts a chunk as "first" when `delta.content` is non-empty.

## 5. Which models this key could use
Several model names in the key's list did not work through the OpenAI-compatible endpoint:
| Model | Result |
|---|---|
| `gemini-3.1-flash-lite`, `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3-flash-preview` | Work |
| `gemma-4-26b-a4b-it`, `gemma-4-31b-it` | Work (they print `<thought>` text) |
| `gemini-2.5-pro`, `gemini-2.5-flash-lite` | **404** although listed |
| `gemini-3.1-pro-preview`, `gemini-pro-latest`, `gemini-3.7-flash` | **429** (no quota on this key / plan) |
| `gemini-flash-latest`, `gemini-3.8-flash` | **503** (overloaded when tried) |

So a name appearing in the model list does not mean it can be called. My earlier suggestion of `gemini-2.5-flash-lite` as the cheapest was wrong for this key: it returned 404. The pro models were not available, so the "large" model here is the larger Flash tier (`gemini-3.6-flash`), plus the 31B Gemma. Always test a model with one small call before relying on it.

## 6. Cautions
- Three runs per model, at one time of day: medians are an indication, not a benchmark.
- TTFT includes the network round trip from this machine to the provider.
- The local model runs on the CPU (the GPU is too small); a machine with a good GPU would change the local numbers a lot.
- Thinking time depends on the prompt; a harder question makes the larger model think longer.
- Prices differ per model; the larger Flash costs several times the small one per token, on top of the extra thinking tokens.

## Quick check
- What is TTFT, and why is it what a chat user feels first?
- Why do the two Gemini models stream at a similar speed but start at different times?
- How can I find the hidden thinking tokens in `usage`?
- Why is one hosted run not enough to judge a model's speed?
- Why can a model in the list still fail when I call it?
