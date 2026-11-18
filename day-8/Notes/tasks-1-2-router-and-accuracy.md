# Day 8 tasks 1 and 2: the intent router and its accuracy

Built in `C:\Projects\ai-eng\ai-service` on the `day-8` branch. Decisions are in `decisions.md` (45 to 51), the traps in `gotchas.md`. Tasks 3 to 5 (cost and latency against always-large, the parallel summaries, the framework rebuild) are not done yet.

## 1. What the router does (task 1)
```
message ─> rules (free) ─hit─────────────────────────────┐
              │ no hit                                    ├─> specialised prompt (a handbook slice) ─> small model answers
              └─> small model: classify_query v5 ─────────┘
                        │ unclear, or a reply that is not a label
                        └─> large model, full handbook ─> answers
```
- `POST /route` returns the answer and a `meta` with the intent, whether a rule matched, the models, latency and tokens per stage. A failed answer call is a clean 502.
- Small model: `gemini-3.1-flash-lite` ($0.25 in, $1.50 out per million tokens). Large model: `gemini-3-flash-preview` ($0.50 in, $3.00 out, thinking included).

## 2. Choosing the small model: `gemma3:270m` does not work
I ran the 60 labelled Day 7 cases through the local 270M model with the router's own prompt, token cap and parser:
| | Correct | Said "unclear" | Confident but wrong |
|---|---|---|---|
| `gemma3:270m` | 14 of 60 (23%) | 12 | **34** |

It answered `admission` for 39 of 60 messages (always answering `admission` would also score 17%). A valid label is not a confidence signal, so its wrong answers stay on the cheap path. With the same prompt, Flash-Lite scored 30/30 on both sets.

## 3. Choosing the large model
- Your free-tier table has no Pro model (2.5 Pro and 3.1 Pro show 0 requests); the Flash models allow 20 requests a day. So the always-large baseline can only be a small sample, about 18 to 20 queries a day.
- `gemma-4-31b-it` was tried: a 503, then a 24 s reply made of `<thought>` text with 0 completion tokens reported. Rejected.
- `gemini-3-flash-preview` works (1.3 s for a one-word reply). It bills thinking as output: prompt 8, completion 1, total 49. The usage code now counts `total_tokens - prompt_tokens`, so its cost is not under-counted.

## 4. Fixes found by checking the first router
| Problem | Fix |
|---|---|
| Greeting rule fired on "Hi, I want the eligibility criteria" and a `refund` rule on "charged twice... please refund": 3 wrong of 15 rule hits on the 60 cases | the greeting rule needs the whole message; `charged twice` and `no access` are complaints; only `refund policy` is fees: 0 wrong of 6 |
| A failed answer call became a 500 | `LLMUnavailableError` (502) |
| The classifier used prompt v4 (twice the cost, replies could be cut at 30 tokens) | `classify_query` v5, token cap 20 |
| v2 cannot say "I don't know", so nothing would ever escalate | v5 adds the `unclear` label |
| The specialised prompts had no institute facts | built from the handbook: `router_<intent>/v2.md`, 3.7K to 13K characters against 20.4K for the full handbook |

## 5. Router accuracy (task 2): 90 of 90
Stage 1 only (rules, then `classify_query` v5 on Flash-Lite): the 30 hard and 30 independent Day 7 cases plus 30 new queries, of which 6 should be escalated.
| Set | Correct | Escalated correctly | False escalations | Confident but wrong | Rules fired (wrong) |
|---|---|---|---|---|---|
| Day 7 hard set | 30/30 | n/a | 0 | 0 | 5 (0) |
| Day 7 independent set | 30/30 | n/a | 0 | 0 | 1 (0) |
| New router queries | 30/30 | 6/6 | 0 | 0 | 0 |
| **All 90** | **90/90** | **6/6** | **0** | **0** | **6 (0)** |

84 classifier calls: median 2.06 s, 416 tokens, $0.000106 per call.

## 6. What this does not prove
- I wrote the `unclear` definition and the six escalation queries together, so they match each other closely.
- The Day 7 sets have no `unclear` label, so only the 6 new queries test escalation.
- A strong model on clear queries scores well; borderline requests written by someone else are still needed.
- The cost and latency comparison against always-large (task 3) is not measured yet.

## Quick check
- Why can the classifier prompt of Day 7 never escalate, and what fixed it?
- Why is "the reply is a valid label" no confidence signal?
- Why is the always-large baseline only a small sample?
- Where do thinking tokens show up in the usage block?
