# Day 8 task 3: the router against always-large, on cost, latency and quality

Measured with `scripts/run_router_cost_eval.py` (results in `scripts/results/router_cost_eval.json`, sample in `scripts/data/router_cost_sample.json`). Small model: `gemini-3.1-flash-lite`. Large model: `gemini-3-flash-preview`. Decisions are in `decisions.md` (52 to 55).

## 1. How it was measured
- **Always-large:** the large model answers with the full handbook (`chat_system` v1), the product's real chat prompt.
- **Router:** the free rules, then the small model classifies (`classify_query` v5) and answers with the intent's handbook slice; an unclear query goes to the large model with the full handbook.
- **A small sample:** the large model allows only 20 free requests a day, so there are **14 queries** (11 with a clear intent, 3 that should be escalated), taken from the three labelled sets. A query that the router escalates **reuses** the always-large call (same model, same prompt), so the router's cost for it is the classifier call plus that call.
- **Cost and latency** come from the accounting layer (the provider call itself, not time waiting in the rate limiter).
- **Quality** is a rubric of facts that the handbook really contains (a price, a percentage, a time, a rule): an item passes when any one of its alternatives appears in the answer; a query's score is the share of items that pass. The same answer cap (1,000 tokens) is used for both flows.

## 2. Results, query by query
| # | Label | Router decided | Escalated | Cost always-large | Cost router | Latency always-large | Latency router | Rubric large | Rubric router |
|---|---|---|---|---|---|---|---|---|---|
| 1 | fees | fees | no | $0.003698 | $0.000751 | 3.3 s | 4.2 s | 1.00 | 1.00 |
| 2 | fees | fees | no | $0.002963 | $0.000858 | 3.3 s | 4.6 s | 1.00 | 1.00 |
| 3 | fees | fees | no | $0.002591 | $0.000802 | 2.7 s | 4.3 s | 1.00 | 1.00 |
| 4 | schedule | schedule | no | $0.002201 | $0.000762 | 2.5 s | 4.5 s | 1.00 | 1.00 |
| 5 | schedule | schedule | no | $0.003475 | $0.000754 | 2.9 s | 4.3 s | 1.00 | 1.00 |
| 6 | academic | academic | no | $0.002892 | $0.000996 | 3.4 s | 4.7 s | 1.00 | 1.00 |
| 7 | academic | academic | no | $0.003027 | $0.001010 | 3.8 s | 5.9 s | 1.00 | 1.00 |
| 8 | admission | admission | no | $0.003164 | $0.000878 | 3.8 s | 5.6 s | 1.00 | 1.00 |
| 9 | complaint | complaint | no | $0.002865 | $0.000485 | 3.8 s | 4.0 s | 0.50 | 1.00 |
| 10 | complaint | complaint | no | $0.003595 | $0.000576 | 4.5 s | 4.1 s | 1.00 | 0.50 |
| 11 | admission | admission | no | $0.003191 | $0.000804 | 3.8 s | 6.8 s | 1.00 | 1.00 |
| 12 | unclear | unclear | yes | $0.004503 | $0.004618 | 6.0 s | 8.1 s | 0.00 | 0.00 |
| 13 | unclear | unclear | yes | $0.003451 | $0.003559 | 4.6 s | 7.1 s | 1.00 | 1.00 |
| 14 | unclear | unclear | yes | $0.004085 | $0.004198 | 5.4 s | 7.0 s | 1.00 | 1.00 |

## 3. Summary
| | Always-large | Router |
|---|---|---|
| Average cost per query | $0.003265 | $0.001504 |
| **Cost saving** | | **53.9%** on this sample (3 of 14 escalated) |
| Cost saving on the 11 clear-intent queries | | **74.2%** |
| Median latency | 3.8 s | 4.63 s |
| p95 latency | 6.03 s | 8.07 s |
| Mean rubric score | 0.893 | 0.893 |

- **Target of the plan (at least 40% cheaper without quality loss): met on cost.** 53.9% cheaper on this sample, and 74.2% cheaper for the queries the router keeps on the small model.
- **Reweighted to the 90-query test mix** (6 of 90 escalated, not 3 of 14), computed from the per-group averages above: always-large $0.003124, router $0.001011, saving **67.6%** (an estimate, not a measurement). The saving depends on how many real requests escalate.
- **Quality: equal on average (0.893 against 0.893), but not identical per query.** The router's complaint prompt asked for the payment details and offered the admissions manager (case 9: router 1.00, always-large 0.50); the always-large answer gave the concrete recording rule (case 10: router 0.50, always-large 1.00). Case 12 scored 0.00 for both: the same answer, cut off (see section 4).
- **Latency: the router is slower**, +0.8 s median (+1.1 s on the 11 clear-intent queries: 4.5 s against 3.4 s) and +2.0 s at p95, because it makes **two sequential calls** (classify about 2 s, then answer) while the large model answers in one call of about 3.4 s. The router buys about 74% lower cost with about a second more latency.

## 4. What the measurement showed about the large model
- **It thinks a lot.** The always-large answers averaged about **544 output tokens** for answers of about 90 tokens of text: roughly **450 tokens per answer are thinking**, billed as output at $3.00 per million. That is why the clear-intent saving is so large. If the model did not think, my estimate for the clear-intent saving is about **59%** instead of 74%, still above the 40% target.
- **A cap of 1,000 tokens truncated one answer.** Case 12 (a request with several problems at once) used 996 of 1,000 output tokens on thinking, and the answer stopped after "here is the information from our policy:". The router's default cap of 512 would cut such answers more often, so the router now has a separate, larger cap for the large model (`large_max_tokens = 2000`, with a test).
- **The prompt carries most of the always-large input cost**: about 4,830 input tokens per query (the full handbook), against 400 to 1,500 for the router's slices.

## 5. What this does not prove
- **Fourteen queries is a pilot.** One query is 7% of the sample, the router and the always-large answers differ in both directions, and no run was repeated (the large model's daily quota is used up).
- The rubric checks facts I chose from the handbook; it does not judge tone, completeness or invented extra claims.
- The three escalation queries are my own and match the `unclear` definition closely.
- The API route is not wired to this large model yet: `POST /route` still takes `small_backend` and `large_backend` as backend names (`hosted` is Flash-Lite), so the large model of this measurement needs a setting of its own before it can be used there.

## Quick check
- Why does the router cost less even though it makes two calls?
- Why is the router slower, and what would shrink the gap?
- Where do about 450 of the large model's 540 output tokens go?
- Why does a thinking model need a larger `max_tokens` than a plain one?
