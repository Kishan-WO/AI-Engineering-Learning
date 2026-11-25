# Two-stage retrieval and the latency budget

Goes with `learning/3.bi-encoders-vs-cross-encoders.md` and `learning/4.re-rankers.md`. This is the day's required diagram note.

## 1. The diagram
```
                          user question
                                |
                 [ optional: rewrite / multi-query / HyDE / filters ]      <- small LLM call, flags
                                |
          +---------------------+----------------------+
          |                                            |
   embed query -> vector search                 keyword search (tsvector)
   (tenant filter in the query)                 (tenant filter in the query)
   top 50, ranks + cosine scores                top 50, ranks + ts_rank scores
          |                                            |
          +---------------------+----------------------+
                                |
                        RRF fusion (k = 60)
                         about 50 candidates
                                |
                  STAGE 1 ends: tuned for RECALL
                                |
                [ re-ranker: score 50 (query, chunk) pairs ]               <- RERANKER flag
                       timeout -> keep fused order
                                |
                  STAGE 2 ends: tuned for PRECISION AT THE TOP
                                |
                     dedupe / cap per section, keep 5
                                |
                      grounded prompt (Day 12) -> LLM
```

## 2. Where the time goes
Every box has its own number, and the budget is the sum (the numbers below are blanks for me to fill, not results):
| Stage | Time to measure | Depends on |
|---|---|---|
| Query transformation (optional) | LLM call latency | model, prompt, output length |
| Embedding the query | one embedding call | API or local model |
| Vector search | database round trip | index, `ef_search`, filter |
| Keyword search | database round trip | GIN index, query length |
| Fusion | microseconds to a millisecond | list sizes |
| Re-ranker (optional) | N pairs scored | `N`, chunk length, hosted or local |
| Generation (Day 12) | TTFT then tokens | model, context size |

**What I measured already on Day 10** (2026-11-25, single runs on my laptop, so not a p95):
| What | Time |
|---|---|
| Embedding the query (Jina API call) | 921 ms, then 509 ms |
| Vector search in PostgreSQL (SQL only, HNSW index scan, 2,097 chunks) | 1.565 ms |
| The whole `POST /api/v1/search` request | 592 ms and 532 ms |

The SQL time is tiny next to the whole request; the embedding call is likely most of it (I did not time the stages inside one request).

**A setting that changes the number of candidates.** I forced the HNSW index on my `chunks` table and asked for 50 rows:
```
hnsw.ef_search = 40 (default), LIMIT 50                 -> 40 rows
hnsw.ef_search = 100,          LIMIT 50                 -> 50 rows
hnsw.ef_search = 40, hnsw.iterative_scan=relaxed_order  -> 50 rows
```
So "top 50" is silently "top 40" with the default setting whenever the index is used. A tenant filter is applied after the index scan, so it can leave even fewer ([pgvector README, filtering](https://github.com/pgvector/pgvector#filtering)). `search_chunks` sets neither setting today. With relaxed order the rows can be slightly out of distance order.

The user waits for everything before the first token. The re-ranker budget (the plan's example: +300 ms p95) is about the **added** time of that one stage.

## 3. How to measure a p95 honestly
- **Enough samples:** a p95 from 5 queries is meaningless. Run the 20 labelled queries many times (for example 10 rounds is 200 timings) and compute the 95th percentile of those. The more samples, the steadier the tail.
- **Time each stage separately** with a timer around each call (the Day 2 `timer()`), and also the total.
- **Warm and cold:** the first call after a start is slower (model loading, connection setup). Report warm numbers and note the cold one.
- **Same machine, same load:** do not run an eval or a build at the same time.
- **Hosted services vary:** the network and provider load change from run to run; run at different times and keep the worst p95.
- **Compare against the flag off:** the added cost is `p95(with) - p95(without)` on the same queries, not a number compared with a memory.
- **Report `N` with every number:** "+210 ms at p95 for `N = 50`" is a result; "+210 ms" is not.

## 4. What the diagram says about failure
| If this fails | The pipeline |
|---|---|
| query transformation | uses the original query |
| keyword search | continues with the vector list only, and logs it |
| vector search | continues with the keyword list only, and logs it |
| re-ranker | keeps the fused order, and logs it |
| both retrievers | returns "search unavailable" (a clear error, not an empty answer) |

Each fallback is a line in the log, so Day 15's dashboard can show how often it happened. (Day 21 builds the formal degradation drill.)

## 5. What to log for task 6
For the final top chunk of every query: the vector rank (or none), the keyword rank (or none), the fused rank, and the re-ranked rank. "Found by vector only / keyword only / both" is then a simple count over the 25 queries, and the exact-code queries should show the keyword list at work.
