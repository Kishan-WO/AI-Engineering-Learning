# Day 11: RAG I: ingestion, parsing and chunking

**Build target (from the plan):** an idempotent ingestion pipeline with three chunking strategies.

The learning notes were written first, as on earlier days, and the build came after. The code, the build log and the measured results are in the `ai-service` repository, branch `day-11` (see its `READING-ORDER.md`).

## Layout
```
day-11/
  README.md      this index
  learning/      the concept notes (written first)
  Notes/         explanations that go with the learning notes
```

## Learning notes (`learning/`)
They follow the plan's "Learn" sections, in order:
| Note | Plan section | What it covers |
|---|---|---|
| `1.the-rag-pipeline.md` | The RAG pipeline | load, parse, clean, chunk, embed, store, retrieve, augment, generate; the offline path against the online path; where quality is lost |
| `2.document-parsing.md` | Document parsing | PyMuPDF and pypdf, layout-aware parsers (Docling, Unstructured, Marker), tables, scanned PDFs and OCR, cleaning headers, footers and hyphenation, keeping structure as metadata |
| `3.chunking-strategies.md` | Chunking strategies | fixed-token with overlap, recursive, structure-aware, semantic, parent-child, contextual headers, and the size trade-off |
| `4.ingestion-engineering.md` | Ingestion engineering | background worker and job status, content hashes and idempotency, versioning, batching embeddings, per-document failure |

## Notes (`Notes/`)
Explanations that go with the learning notes, numbered in reading order:
| Note | Goes with | What it covers |
|---|---|---|
| `01-idempotent-ingestion-explained.md` | `learning/4.ingestion-engineering.md`, sections 2 and 3 | the three hashes (file, chunk id, pipeline version), what "re-ingest does nothing" means in code, and how a re-ingest after a chunker change replaces old chunks without a gap |

## Tasks (from the plan, done)
The details, commands and outputs are in `ai-service`, `notes/day-11/README.md`.

| Task | What | Result |
|---|---|---|
| **1** | `POST /ingest` (file or URL) enqueues a worker job: parse, clean, chunk, embed, upsert. A status endpoint | done, with ARQ as the queue. A real download from the internet through a link is **not tested** |
| **2** | Three chunkers: fixed-token with overlap, recursive, Markdown/structure-aware | done: of 28 Markdown tables, 14 were not whole in any chunk with fixed-size, and 4 with each of the other two |
| **3** | Contextual headers (document title + section path) on each chunk, as an option | done, off by default; the effect on search is **not measured** |
| **4** | Parse 5 difficult PDFs (tables, two columns, a scanned page); record what broke | done: 4 papers and a scan I made from a page, not a real scan. The failures are recorded, not fixed |
| **5** | Break it on purpose: split a table over two chunks, ask a question that needs both halves, show that retrieval returns only half | done, with a caveat: with 5 results search found **none** of either table; in the first 10 (looked at afterwards) it had 5 of 7 and 8 of 22 rows. The splits came from the normal chunk size |
| **6** | Re-ingest the whole corpus and prove zero duplicate chunks | done: 234 documents, 4,683 chunks, no duplicates |
| Notes | A parsing failure catalogue | done: `ai-service`, `notes/day-11/parsing-failure-catalogue.md` |
| Done when | I can re-run ingestion on the whole corpus and the `chunks` table does not change | met: the second run wrote 0 chunks and the table was identical |

## What earlier days already give me
- **A service with tenants, users and documents:** `ai-service` has `documents` with a `content_hash` (SHA-256 of the file bytes) and a unique `(tenant_id, content_hash)`, JWT login that gives every request a tenant, and an upload route (`.txt`, `.md`, `.pdf`, up to 20 MB). The route already extracts PDF text with `pypdf` inside the request, stores **only the extracted text** (not the file), and answers a duplicate with an error that carries the existing document's id.
- **Docker Compose with `redis`:** the service is already in the file. There is no ARQ or Celery package yet. The worker is one more service next to `api`.
- **The `chunks` table (Day 10):** built with an HNSW index, loaded with the 2,097 Day 9 sections (`scripts/upsert_corpus.py`) and searched by `POST /api/v1/search`. Today's upsert writes into it. See "Where the build stands" below for what it does not have yet.
- **Embedding code from Day 9:** Jina `jina-embeddings-v3` (1,024 dimensions) and BGE-M3, batching and rate-limit handling (`Notes/06-embedding-batching-and-rate-limits.md`).
- **A first chunking attempt (Day 9):** 234 documents cut by heading into 2,097 sections (`Notes/04-chunk-sizing-and-splitting.md`). Today replaces that with real chunkers.
- **The `@retry` decorator (Day 2) and the semaphore habit:** every embedding call in the worker uses both.
- **A measuring habit:** every result gets a number and its limit. For chunking the real test comes on Day 12 (10 questions against all three chunkers) and Day 14 (the golden set).

## Where the build stands before Day 11 (checked 2026-11-25)
This is how it looked **before** the Day 11 build. The results are in the task table above.

| Item | State | What it means today |
|---|---|---|
| Day 10 tasks 1 to 3 | built in `ai-service` on branch `day-10`, **not committed yet** | the Day 11 branch has to start from this work |
| Day 10 tasks 4 and 5 (recall and `ef_search`; Qdrant behind `VectorStore`) | **not built** | there is no `VectorStore` protocol to write into yet |
| `chunks` columns | `id`, `tenant_id`, `document_id`, `chunk_index`, `heading`, `text`, `text_hash`, `embedding`, `embedding_model`, `metadata` | no pipeline version column, no page number, no block type |
| `chunks` uniqueness | `UNIQUE (document_id, chunk_index)` | it affects how a re-ingest writes (`Notes/01`, section 4) |
| `scripts/upsert_corpus.py` | upserts, deletes nothing | if a new chunker made fewer chunks, the extra old rows would stay |
| Job table and worker | none | new in task 1 |

## Points to settle at the start of the build
- **Which job queue?** ARQ is in maintenance-only mode (note 4, section 1). I choose ARQ or Celery knowing that, and write the reason in `decisions.md`.
- **Where is the original file kept?** Today only the extracted text is stored. A new parser version can re-parse only if I keep the file.
- **Where does the uploaded file wait for the worker?** The job should carry a file id or path, not the bytes. A shared Docker volume is enough for now; object storage is the later answer.
- **Which tokenizer counts the tokens?** The embedding model's own, so "512 tokens" means what the model sees. Hindi costs more tokens than English (Day 4), so a character count would give uneven chunks.
- **What is the chunk ID?** It must be stable between runs and change when the text or the pipeline changes (note 4 and `Notes/01`).
- **Which parser first?** PyMuPDF for speed, Docling for the hard PDFs, and a rule for when to fall back (task 4 gives the rule its numbers).
- **How do I tell a scanned page from an empty one?** The text length per page, with a threshold I choose by looking at my 5 difficult PDFs.
