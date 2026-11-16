# Day 6: LLM integration II: reliability, cost and provider abstraction

Build target: a production-shaped LLM layer that survives 50 messy inputs. Done when `/extract` survives all 50 with zero unhandled parse errors.

As in Day 5, the tasks are one feature, so they will be built directly into `ai-service` (`C:\Projects\ai-eng\ai-service`). This folder holds the learning notes and the evidence.

## Layout
```
day-6/
  README.md      this index
  learning/      the concept notes (written first)
  Notes/         what was built and the real results (after the build)
```

## Learning notes (`learning/`)
| Note | Topic |
|---|---|
| `1.error-handling.md` | 429 and `retry-after`, 5xx, timeouts, context-length and refusals, retry or fail fast, backoff with jitter, circuit breaker, fallback |
| `2.token-accounting-and-cost.md` | `usage` from every response (input, output, cache read and write), cost from a price table, per tenant, user and feature, budgets and alerts |
| `3.prompt-caching.md` | Stable prefix first, explicit markers vs automatic caching, measuring the hit rate from usage |
| `4.provider-abstraction.md` | `LLMClient` Protocol (`generate`, `stream`, `generate_structured`), adapters, wrappers, semaphore per provider, LiteLLM or OpenRouter, batch APIs |

## Tasks (from the plan)
| Task | What | Status |
|---|---|---|
| **1** | `LLMClient` protocol with two provider adapters plus an Ollama adapter, chosen through settings | done (OpenAI-compatible and Ollama run live; Anthropic tested against a fake server only) |
| **2** | Middleware or wrapper that logs per request: model, input, output and cached tokens, cost, latency, request ID, tenant | done, JSON log line plus an `llm_calls` row per provider call |
| **3** | Retry on transient errors with backoff; fall back to a second provider after N failures | done, verified live (a real 429 burst and a dead provider) |
| **4** | Retry-on-validation-failure loop for `/extract`: send the Pydantic error back to the model, at most 2 retries | done, one real repair seen |
| **5** | A file of 50 messy inputs (empty, very long, wrong language, emojis, contradictory data, prompt injection, Hinglish) | done, `ai-service/scripts/messy_inputs.py` |
| **6** | Run all 50 through `/extract` and report: valid, repaired after retry, correctly refused, failed | done, hosted and local |
| **7** | Prompt caching on the `/chat` system prompt; show cache-read tokens in the logs | done, cache hits from turn 2 |
| Notes | A cost model table | done, `Notes/tasks-1-7-reliability-cost-providers.md` |

## What Day 5 already gives me
- `LLMProvider` protocol and `OpenAICompatProvider` (Gemini and Ollama) in `services/llm.py`, with a registry built from settings.
- One validation retry in `/extract` (task 4 grows this to at most 2 with a clearer repair prompt) and `LLM_MAX_RETRIES=1` from the SDK (task 3 replaces it with my own retry).
- A hosted-vs-local comparison script (`scripts/compare_extract.py`), which is the starting point for the 50-input run.
- Free-tier limits of the hosted model: 15 RPM, 250K TPM, 500 RPD (from my AI Studio page), which decide the concurrency limit.
