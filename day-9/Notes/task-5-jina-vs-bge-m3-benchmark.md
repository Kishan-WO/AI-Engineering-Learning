# Day 9 task 5: benchmark of an API embedding model against an open one

Script: `scripts/benchmark.py`. Saved results: `results/benchmark_results.json` (per query: the top 5 rows and hit flags for both models), `results/jina-embeddings-v3_meta.json`, `results/bge-m3_meta.json`. Queries: `scripts/queries.json` (task 4).

## 1. What was compared
| | API model | Open model |
|---|---|---|
| Model | Jina `jina-embeddings-v3` | `BAAI/bge-m3` (sentence-transformers) |
| Where it runs | Jina's servers | my computer, CPU only |
| Dimensions | 1,024 | 1,024 |
| Corpus input | heading path + text, `task=retrieval.passage` | the same text; the script asks for `prompt_name="passage"` and falls back to plain encoding if the model has no such prompt |
| Query input | `task=retrieval.query` | `prompt_name="query"`, with the same fallback |
| Corpus | the same 2,097 sections | the same 2,097 sections |
| Queries | the same 20 | the same 20 |

## 2. The result (20 queries, lenient document-level rule)
| Metric | Jina v3 | BGE-M3 |
|---|---|---|
| Recall@1 | 14/20 (70%) | 11/20 (55%) |
| Recall@3 | 19/20 (95%) | 17/20 (85%) |
| Recall@5 | 19/20 (95%) | 18/20 (90%) |
| MRR | 0.8083 | 0.7097 |
| Hindi or Hinglish queries (5), recall@5 | 5/5 | 5/5 |
| Embedding the 20 queries | 1,136 ms (API), 555 tokens | 875 ms (local, model already loaded) |
| Embedding the corpus | 910 s in all, 235 s in API calls, 1,270,018 tokens | 12,541 s (3.5 hours) |
| Cost | $0 (free tier) | $0 (local) |

- If Jina were billed at $0.02 per million tokens (the figure `benchmark.py` uses for its cost line; I did not check it against Jina's price page), the whole corpus would cost about $0.025 and the 20 queries a fraction of a cent.
- **The rank of the first correct page for every query** (">5" means not in the top 5):

| Q | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Jina | 3 | 1 | 2 | 1 | 1 | 1 | 3 | 1 | 1 | 1 | 1 | 1 | 2 | >5 | 1 | 2 | 1 | 1 | 1 | 1 |
| BGE-M3 | >5 | 1 | 2 | 1 | 2 | 1 | 3 | 2 | 4 | 1 | 1 | 1 | 2 | >5 | 1 | 2 | 1 | 1 | 1 | 1 |

## 3. What it shows
- **Recall@5 is close:** 19 against 18 of 20, a gap of one query. **At the top the gap is wider:** Jina puts a correct page first in 14 queries and BGE-M3 in 11, so the MRR is 0.81 against 0.71. Three queries out of 20 is suggestive, not proven (one query is 5 points).
- **They differ on a few queries:** BGE-M3 does not find the path-parameter page (Q1) in the top 5, where Jina has it at rank 3. Jina finds the computed-fields page (Q9) and the BaseModel page (Q8) at rank 1; BGE-M3 at ranks 4 and 2.
- **Hindi and Hinglish work in both:** all five were found in the top 5, including the Devanagari one (Q19) and the Hinglish Chemistry question (Q18), both at rank 1.
- **Cost and speed are the real difference:** BGE-M3 is free and keeps the text on my machine, but embedding the corpus took 3.5 hours on a CPU against about 15 minutes for Jina (4 minutes of actual API time). A query is fast with the model loaded (about 55 ms) but a fresh `search.py` run takes about 9 s because it loads the model.
- **Both fail on the same queries** (Q14, and ranks 2 or 3 on Q3, Q7, Q13, Q16). Task 6 explains three of them.

## 4. The first benchmark run was wrong
The first run scored Jina 70% and BGE-M3 75% at recall@5, and had BGE-M3 ahead at recall@1 (60% against 45%), at recall@5 and in MRR (0.67 against 0.59), with recall@3 equal at 70%. That run counted any section of a source as correct whenever a title did not match, which made 7 queries nearly impossible to miss. After I rebuilt the labels (task 4) the picture reversed at the top: Jina ahead at recall@1 and MRR. The first numbers should not be quoted.

## 5. Limits
- **20 queries.** One query is 5 percentage points; a difference of one or two queries is noise. I did not compute a confidence interval.
- **I wrote the queries and the labels**, and I had seen the first results before rewriting some of them (task 4 explains how I limited that).
- **One run per model, one corpus, CPU only.** The BGE-M3 corpus time depends on my computer; a GPU would make it far faster.
- **Different input handling:** Jina is told whether a text is a document or a query. For BGE-M3 the script asks for the "passage" and "query" prompts and silently falls back to plain encoding when the model does not define them; BGE-M3 normally needs no prefix, so most likely none was applied. **I did not check which path ran**, so I cannot say that BGE-M3 got a query form the way Jina did.
- The corpus is 57% Chemistry textbook by words, and only 3 of the 20 queries use it.

## Quick check
- Which metric separates the two models, and which does not?
- Why can the 3.5 hours for BGE-M3 not be compared directly with Jina's 15 minutes?
- Why should the first benchmark numbers not be quoted?
