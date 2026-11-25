# Day 10: Vector databases

**Build target (from the plan):** `POST /search` (semantic, tenant-isolated) on pgvector, ported to Qdrant.

Today starts with the learning notes (written first, as on earlier days). The build and the results come after.

## Layout
```
day-10/
  README.md      this index
  learning/      the concept notes (written first)
  Notes/         what was built and the measured results (after the build)
```

## Learning notes (`learning/`)
They follow the plan's "Learn" sections, in order:
| Note | Plan section | What it covers |
|---|---|---|
| `1.why-a-vector-database.md` | Why a vector database | exact search is O(n), approximate nearest neighbour (ANN) trades a little recall for speed, and when brute force is still fine |
| `2.options.md` | Options | pgvector, Qdrant, Chroma, Weaviate, Pinecone, Milvus, LanceDB, FAISS (a library, not a database), and the MongoDB and Elasticsearch options; how I choose |
| `3.indexes-hnsw-and-ivfflat.md` | Indexes | how HNSW works, `m`, `ef_construction`, `ef_search`, the recall and speed trade-off, IVFFlat, build time and memory |
| `4.indexing-and-upserts.md` | Indexing and upserts | upsert by a stable chunk id, deleting vectors with their document, re-indexing when a document or the embedding model changes, storing the model name with each vector |
| `5.metadata-filtering.md` | Metadata filtering | pre-filtering against post-filtering, why post-filtering can return too few results, pgvector iterative scans and Qdrant payload indexes |
| `6.multi-tenancy.md` | Multi-tenancy | tenant column plus filter, collection per tenant, payload partitioning, and why isolation must be inside the query |

## Notes (`Notes/`)
Explanations that go with the learning notes, numbered in reading order:
| Note | Goes with | What it covers |
|---|---|---|
| `01-pgvector-syntax-and-index-build-explained.md` | `learning/3.indexes-hnsw-and-ivfflat.md`, sections 3 and 5 | the pgvector SQL line by line (extension, `vector(1024)`, the HNSW index and its operator class, `ef_search`, the distance query), distance against similarity, the dimension limit, and why an HNSW build is slow and how much memory it needs |

## Tasks (from the plan, not started)
| Task | What |
|---|---|
| **1** | Add a `chunks` table with a vector column and an HNSW index (pgvector); store chunk text, document id, tenant id, metadata and the embedding model name |
| **2** | Embed and upsert the corpus with a script (it moves to a background worker on Day 11) |
| **3** | `POST /search`: embed the query, search with the tenant filter, return chunks with scores. No LLM yet |
| **4** | Measure recall@5 against yesterday's 20 queries; compare HNSW with exact search; tune `ef_search` |
| **5** | Port the same index to Qdrant behind a `VectorStore` protocol; switch by config |
| **6** | Isolation test: a query from tenant 2 can never return tenant 1 chunks, including when tenant 2 has zero documents |
| **7** | Delete a document and prove its vectors disappear |
| Notes | A pgvector against Qdrant note |
| Done when | I can find a document using words that never appear in it |

## What earlier days already give me
- **A service with tenants and documents:** `ai-service` already has `tenants`, `users`, `documents` (with a `content_hash`), JWT login that gives every request a tenant, async SQLAlchemy and Alembic migrations. The `chunks` table, its tenant column and its foreign key to `documents` fit straight into it.
- **A Postgres that can already do vectors:** the compose file uses the `pgvector/pgvector:pg16` image, so the extension is there; a migration only has to run `CREATE EXTENSION vector`.
- **A corpus and its vectors from Day 9:** 234 documents cut into 2,097 sections, embedded with Jina `jina-embeddings-v3` (1,024 dimensions, length 1) and with BGE-M3 (1,024 dimensions). 1,024 is below pgvector's index limit.
- **A baseline to beat or match:** exact NumPy search over those vectors takes 0.5 to 0.7 ms, and on the 20 labelled queries Jina gets recall@5 of 95% (19 of 20), MRR 0.81. HNSW is judged against these numbers.
- **The measuring habit:** a labelled query set, a script that prints every field, a note with the real numbers and the limits next to each percentage.
- **A gotcha from the last days:** the `api` container copies `alembic/` into its image when it is built, so a new migration needs `docker compose up -d --build api`, or the container crashes with "Can't locate revision".

## Points to settle at the start of the build
- **Which vectors go in the table?** Jina (API, needs the key at search time) or BGE-M3 (local, needs the model loaded). The query must come from the same model as the stored vectors. I'd start with Jina, store the model name and version in each row, and keep the second model for later.
- **How many dimensions?** The full 1,024. The table has one fixed size, so changing it means a new column or table.
- **Where do the chunks come from?** The Day 9 sections, loaded by a script. They carry their document and source, but the tenant is new: I need a rule for which tenant owns the corpus, and a second tenant for the isolation test.
- **Is a vector database needed at all at this size?** At 2,097 vectors, no: NumPy is exact and fast. Today is about the engineering around it (filters, tenants, upserts, deletes, a swappable store), not about speed.
