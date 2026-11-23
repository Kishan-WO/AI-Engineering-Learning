# Day 9: Embeddings

**Build target (from the plan):** an embedded corpus and a hand-written NumPy semantic search.

Today starts with the learning notes (written first, as on earlier days). The build and the results come after.

## Layout
```
day-9/
  README.md      this index
  learning/      the concept notes (written first)
  Notes/         what was built and the measured results (after the build)
  corpus/        the corpus: manifest, download script, README (the files themselves are not committed)
  scripts/       the task scripts: load_corpus.py, embed_jina.py, search.py, benchmark.py, detect_near_duplicates.py, and queries.json
  results/       the saved results of the tasks (benchmark, near-duplicate pairs, embedding-run metadata, example searches); vectors and corpus text are not committed
  pyproject.toml the Python environment (uv sync)
```

## Learning notes (`learning/`)
They follow the plan's "Learn" sections, in order:
| Note | Plan section | What it covers |
|---|---|---|
| `1.numpy-essentials.md` | NumPy essentials | arrays, `shape`, `dtype` (float32 against float64), broadcasting, `@` and `np.dot`, `np.linalg.norm`, normalising rows, `argsort` against `argpartition`, saving and loading `.npy` |
| `2.what-an-embedding-is.md` | What an embedding is | text to a fixed-length vector, similar meaning gives nearby vectors, an embedding model against a chat model, queries against documents (prefixes and input types) |
| `3.similarity-metrics.md` | Similarity metrics | cosine, dot product (equal to cosine on normalised vectors), Euclidean distance, which metric each model expects |
| `4.embedding-models.md` | Embedding models | API models (OpenAI, Cohere, Voyage, Gemini), open models (BGE-M3, E5, Nomic, GTE, sentence-transformers), multilingual support for Hindi, max input length, cost, throughput, batching |
| `5.choosing-a-model.md` | Choosing a model | the MTEB leaderboard as a starting point, my own queries as the real test, recall@k on 20 queries, how little 20 queries can prove |
| `6.dimensions.md` | Dimensions | storage, memory and latency cost of dimension size, Matryoshka truncation, int8 and binary quantisation |
| `7.use-cases.md` | Use cases | semantic search, classification, clustering, deduplication, recommendation, anomaly detection |

## Notes (`Notes/`)
Worked explanations that go with the learning notes, and the notes of the tasks:
| Note | Goes with | What it covers |
|---|---|---|
| `topk-argsort-vs-argpartition.md` | `learning/1.numpy-essentials.md`, section 6 | the top-k step with a worked example: why the minus sign, `argsort` against `argpartition`, sorting only the `k` winners, cost, and the two things to watch |
| `recall-at-k-and-mrr.md` | `learning/5.choosing-a-model.md`, sections 4 and 5 | how to score a search system: recall@k (hit rate against share found), MRR with a worked example, what to report, and the chunk against document question |
| `renormalising-after-truncation.md` | `learning/6.dimensions.md`, section 4 | why a truncated vector has length below 1, a 2-document example where the plain dot product ranks wrongly, and the two lines that fix it |
| `rag-architecture-and-embeddings.md` | the whole day | how the vectors reach a chat model (they do not, only the retrieved text does), the full RAG architecture with its parts and the days that build them, why a vector only matches vectors from the same embedding model, and what to re-embed when something changes |
| `task-1-load-the-corpus.md` | task 1 | what the loader does, the real counts (234 documents, 2,097 sections), the rules and why, and what the numbers showed |
| `task-2-embed-the-corpus.md` | task 2 | why Jina, how the batching and pacing work, the real run (116 batches, 1,270,018 tokens, 235 s of API time), and what the trial run found |
| `task-3-numpy-search.md` | task 3 | the NumPy-only `search(query, k)`, real example output for both models, and timings |
| `task-4-the-20-queries.md` | task 4 | the 20 queries with their correct documents, the rule for a hit, and what was wrong with the first labels |
| `task-5-jina-vs-bge-m3-benchmark.md` | task 5 and the model comparison | recall@1, @3, @5, MRR, Hindi results, latency and cost for both models, and why the first run was wrong |
| `task-7-near-duplicates.md` | task 7 | the threshold, the bug in the first version, the 15 pairs at 0.97 and how the count changes with the threshold |
| `task-6-queries-where-both-models-fail.md` | task 6 | three queries where Jina and BGE-M3 both fail (Q14, Q07, Q16), what each returned and why |
| `chunk-sizing-and-splitting.md` | `scripts/load_corpus.py` | why long sections (>1500 words) are split, `PART_WORDS = 1000` target sizing, and sentence boundary detection |
| `embedding-batching-and-rate-limits.md` | `scripts/embed_jina.py` | dual-ceiling batching (`BATCH_TEXTS = 32`, `BATCH_TOKENS = 12_000`), rate-limit math, and HTTP timeout prevention |

## Tasks (from the plan)
| Task | What |
|---|---|
| Corpus | Choose the course corpus now: 200+ documents, some PDFs with tables, some Markdown, a licence that allows use. It is used until Day 21 |
| **1** (done) | Load 200+ corpus documents (split long ones by heading for now). **Done:** 234 documents, 2,097 sections (`Notes/task-1-load-the-corpus.md`) |
| **2** (done) | Embed them with one API model in batches; store the vectors as `.npy` plus a metadata JSON. **Done:** Jina v3, 2,097 sections, 1,270,018 tokens (`Notes/task-2-embed-the-corpus.md`) |
| **3** (done) | Write `search(query, k)` with only NumPy: normalise, matrix multiply, `argpartition`. **Done:** `scripts/search.py` (`Notes/task-3-numpy-search.md`) |
| **4** (done) | Write 20 real queries with the known correct document for each. **Done:** `scripts/queries.json` (`Notes/task-4-the-20-queries.md`) |
| **5** | Benchmark two embedding models (one API, one open via `sentence-transformers`) on recall@5, latency and cost; include 5 Hindi or Hinglish queries. **Done:** Jina recall@5 95%, BGE-M3 90% (`Notes/task-5-jina-vs-bge-m3-benchmark.md`) |
| **6** (done) | Find 3 queries where both models fail and explain why. **Done:** Q14, Q07, Q16 (`Notes/task-6-queries-where-both-models-fail.md`) |
| **7** (done) | Detect near-duplicate documents with a similarity threshold. **Done:** 15 pairs at 0.97 (`Notes/task-7-near-duplicates.md`) |
| Notes (done) | The embedding-model comparison note: `Notes/task-5-jina-vs-bge-m3-benchmark.md` |

## What earlier days already give me
- **A service to build into:** `ai-service` (FastAPI, async SQLAlchemy, auth with tenants, `/documents` upload for `.txt`, `.md` and `.pdf`, a stored `content_hash`, a Docker Postgres on port 5433). Day 9 itself is a NumPy exercise in scripts, and the search endpoint on a vector database is Day 10.
- **The measuring habit from Day 7 and 8:** a labelled test set, a script that prints every field, the tables with the real numbers, and the caveats next to each percentage (one query is 5 points out of 100 on 20 queries).
- **Cost and latency accounting:** the `llm_calls` table and `compute_cost()` handle chat models; an embedding call has input tokens only and no output, so it needs its own small cost line.
- **A free-tier habit:** the hosted Gemini key has daily and per-minute limits, which decide how a 200-document embedding run is batched and paced.

## Points to settle at the start of the build
- **Which corpus?** The plan recommends a mix: the FastAPI and Pydantic documentation in Markdown (MIT licensed, and I already know the content, so judging the answers is easy) plus NCERT chapter PDFs (tables, formulas, headings, and the real parsing pain from Day 11). The NCERT licence has to be checked before the files go into a repository.
- **Which two models for the benchmark?** One API model (Gemini embeddings or OpenAI `text-embedding-3-small`, depending on which key and free tier I have) and one open multilingual model (`BAAI/bge-m3` is the natural choice because the test includes Hindi and Hinglish).
- **Where the test queries come from.** They have to be written by me, from the documents, with the right document recorded before any model is run, as with the router queries.
