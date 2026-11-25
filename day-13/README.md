# Day 13: Hybrid search, re-ranking and query transformation

**Build target (from the plan):** BM25 + vector + RRF + an optional re-ranker, all behind config flags.

Today starts with the learning notes (written first, as on earlier days). The build and the results come after.

## Layout
```
day-13/
  README.md      this index
  learning/      the concept notes (written first)
  Notes/         what was built and the measured results (after the build)
```

## Learning notes (`learning/`)
They follow the plan's "Learn" sections, in order:
| Note | Plan section | What it covers |
|---|---|---|
| `1.keyword-search.md` | Keyword search | BM25 intuition, why vector search misses exact identifiers, Postgres full-text search against `bm25s` against Elasticsearch, Hindi and mixed-script tokenisation |
| `2.fusion.md` | Fusion | Reciprocal Rank Fusion, why scores cannot be compared, weighted fusion (awareness) |
| `3.bi-encoders-vs-cross-encoders.md` | Bi-encoders versus cross-encoders | how each reads a query and a document, why the cross-encoder only sees a shortlist, ColBERT (awareness) |
| `4.re-rankers.md` | Re-rankers | hosted and open re-rankers, two-stage retrieval, the latency budget, failing open |
| `5.query-transformation.md` | Query transformation | rewriting, multi-query, HyDE, decomposition, metadata extraction into filters, and the cost of each |

## Notes (`Notes/`)
Explanations that go with the learning notes, numbered in reading order:
| Note | Goes with | What it covers |
|---|---|---|
| `01-rrf-worked-example.md` | `learning/2.fusion.md` | one RRF calculation by hand with real numbers, the effect of `k`, ties, and what RRF cannot see |
| `02-two-stage-retrieval-and-latency-budget.md` | `learning/3` and `learning/4` | the two-stage diagram (the day's required note), where each stage's time goes, and how to measure a p95 honestly |

## Tasks (from the plan, not started)
| Task | What |
|---|---|
| **1** | Add a keyword retriever next to the vector search; fuse the two with RRF |
| **2** | Add a re-ranker behind `RERANKER=none\|cohere\|bge` |
| **3** | Add query rewriting and multi-query behind flags |
| **4** | Write 5 queries with exact codes, IDs or names; confirm that hybrid beats pure vector on them |
| **5** | Measure the latency of each stage; the re-ranker must stay within the budget |
| **6** | Log, for each query, which stage found the final top chunk (vector, keyword, both) |
| Notes | A two-stage retrieval diagram |
| Done when | every stage can be switched off with a flag, and each one has a latency number and a quality number next to it |

## What earlier days already give me
- **Vector search with tenant isolation (Day 10):** `POST /api/v1/search`, with the tenant filter inside the query. The keyword retriever must obey the same rule. The `VectorStore` protocol (Day 10, task 5) is not built yet.
- **`/ask` (Day 12):** retrieve, grounded prompt, streamed answer, checked citations. Today's retriever replaces the "retrieve" box without changing the rest, so the retriever sits behind one function with flags.
- **The standalone-query rewrite (Day 12):** it already makes one cheap LLM call. Query rewriting today is a different goal (a better query, not only a standalone one) and must not be run twice on top of it.
- **Day 9 numbers:** the 20 labelled queries, Jina recall@5 95% (19 of 20) and MRR 0.81. Of the 3 failure cases I studied, only **Q14** is a miss in the top 5 for both models; in Q07 and Q16 the right page is at rank 3 and 2. None of the three is an exact-code query, and the Q14 section does not even contain the words "enthalpy", "formation" or "water", so keyword search should not be expected to fix it. Those numbers are my quality baseline and my first test set for today.
- **Day 12 hand scores:** 10 questions scored on three chunkers. A config change today can be checked against them while the golden set (Day 14) does not exist.
- **The prompt registry, `LLMClient` and the small model (Days 6 to 8):** every query transformation is a registered prompt, a logged call and a cheap model.
- **The latency habit (Day 4):** TTFT and total time per call. Today I measure per stage and use p95, not the average.

## Points to settle at the start of the build
- **Keyword engine:** Postgres full-text search (one database, tenant filter in the same `WHERE`, a GIN index) or `bm25s` in memory. I start with Postgres: isolation is then the same mechanism as Day 10. `bm25s` can be a comparison.
- **Text search configuration:** my PostgreSQL 16 has a `hindi` configuration as well as `english` and `simple` (note 1, section 4). I compare them on English, Hindi and Hinglish queries and exact codes, and write down what happens.
- **How are the query words combined?** `websearch_to_tsquery` needs **all** words to match, which gave 0 rows for a normal question on my corpus (note 1, section 3).
- **How many candidates per retriever and after fusion?** For example 50 from each, fused to 50, re-ranked, 5 kept. These are numbers I vary, not facts. **With the default `hnsw.ef_search = 40`, an HNSW scan with `LIMIT 50` returned only 40 rows** on my table, so I raise `ef_search` to at least the candidate count or switch on iterative scans (`Notes/02`, section 2).
- **The latency budget:** the plan's example is +300 ms at p95 for the re-ranker. I write my own number first, then measure against it.
- **Which re-rankers:** one hosted (Cohere or another) and one open (`bge-reranker-v2-m3`), both multilingual, behind the flag.
- **What the p95 is computed from:** at least a few hundred timed calls, not 5 queries (`Notes/02`).
- **The threshold from Day 12** is a cosine threshold and means nothing on an RRF score. I decide where "nothing relevant" is decided now.

## Dependencies to remember
- A new migration (a `tsvector` column and a GIN index on `chunks`) needs `docker compose up -d --build api`, the gotcha from Day 10.
- The re-ranker needs a key (hosted) or a model download (open); both go in `.env` and not in git.

## What this day does not do
No full evaluation with the golden dataset (Day 14), so today's claims are limited to my 20 + 5 queries and I say so. No tracing UI (Day 15), only the logs. No semantic cache (Day 21).
