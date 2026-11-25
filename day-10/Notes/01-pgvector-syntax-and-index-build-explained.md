# pgvector syntax and index build time and memory, explained

This note explains two parts of `learning/3.indexes-hnsw-and-ivfflat.md`: the pgvector SQL (section 3) and the build time and memory (section 5), piece by piece.

## Part 1: the pgvector SQL, line by line

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE chunks (
    id uuid PRIMARY KEY,
    embedding vector(1024) NOT NULL,
    ...
);

CREATE INDEX chunks_embedding_hnsw
ON chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

SET hnsw.ef_search = 100;                       -- per session or per transaction
SELECT id, embedding <=> :q AS distance
FROM chunks ORDER BY embedding <=> :q LIMIT 5;
```

**`CREATE EXTENSION IF NOT EXISTS vector;`**
- pgvector is an add-on to Postgres. This line switches it on in the database and adds the `vector` column type and the distance operators.
- It runs once per database. It works because the compose file uses the `pgvector/pgvector:pg16` image. In the project it goes in an Alembic migration.

**`CREATE TABLE chunks ( id uuid PRIMARY KEY, embedding vector(1024) NOT NULL, ... );`**
- `chunks` is the table that holds the corpus sections.
- `vector(1024)` is a column that holds exactly 1,024 numbers, the size of a Jina vector. Inserting a vector of another size is an error. That is why a different model with a different size needs a new column or table.

**`CREATE INDEX chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);`**
- `chunks_embedding_hnsw` is the index name.
- `USING hnsw` is the kind of index, the graph index.
- `(embedding vector_cosine_ops)` says which column to index and **which distance the index is built for**. Here it is cosine. An index is built for one kind of distance.
- `WITH (m = 16, ef_construction = 64)` are the two build settings: how many links each point keeps, and how thorough the build is. These are the defaults.

**`SET hnsw.ef_search = 100;`**
- This is the search setting. A bigger number means the search looks at more candidates, so recall goes up and the query gets slower. The default is 40.
- It applies to the session. I can set it per query without rebuilding the index, which is why it is the one I tune.

**`SELECT id, embedding <=> :q AS distance FROM chunks ORDER BY embedding <=> :q LIMIT 5;`**
- `:q` is a placeholder for the query vector, the question after it has been embedded.
- `<=>` calculates the cosine distance between each row's vector and the query. `ORDER BY ... LIMIT 5` returns the 5 closest.
- The index is used only for this shape: `ORDER BY` the distance operator, with a `LIMIT`.

### The four bullets under it
1. **The operator, the operator class and the metric must agree.**

| Distance | Operator in the query | Operator class in the index |
|---|---|---|
| cosine | `<=>` | `vector_cosine_ops` |
| Euclidean (L2) | `<->` | `vector_l2_ops` |
| negative inner product | `<#>` | `vector_ip_ops` |

   If the query uses `<=>` but the index was built with `vector_l2_ops`, Postgres cannot use the index. It silently reads every row. The answer is still correct, since it is an exact scan, but it is slow and gives no error.

2. **Distance is not similarity.** Cosine distance is `1 - cosine similarity`, and smaller means closer. For example, a similarity of 0.76 is a distance of 0.24. To show a score to a user, convert it: `1 - distance`.

3. **Why cosine and inner product give the same order for me.** My vectors are all length 1 (Jina's are exactly 1.0), and for unit vectors the inner product equals the cosine. So the ranking is the same.

4. **The dimension limit.** From memory, pgvector can index a `vector` column of up to 2,000 numbers, or a `halfvec` column (half-precision, 2 bytes per number) of up to 4,000. My 1,024 fits. Gemini's default 3,072 would not have fitted. I confirm this in the README of the version I install.

## Part 2: build time and memory

- **HNSW takes a long time to build.** Every vector added has to search the graph to find its neighbours and then link to them. A bigger `m` and `ef_construction` make that slower. IVFFlat only has to assign each vector to the nearest group, so it is much quicker. For my 2,097 vectors I expect seconds, but I have not measured it.
- **Memory.** The index keeps the links between points. At `m = 16`, each point has about 32 links at the bottom layer, 4 bytes each, so about 128 bytes plus some overhead. Compare that with the vector itself: 1,024 numbers x 4 bytes = **4,096 bytes**. So the graph is small next to the vectors. For a million vectors that would be about 4 GB of vectors and a few hundred MB of graph, by my rough estimate. For the search to stay fast, the vectors and the index should fit in memory, because reading them from disk is far slower.
- **Postgres settings for a build.**
  - `maintenance_work_mem` is the memory an index build may use. If the graph fits, the build is much faster.
  - Parallel workers can share the build.
  - "I read the build notice" means Postgres prints a message when a build runs out of memory, and I should read it.
- **After the build.** New inserts are added to the graph, and deleted rows leave gaps. Many changes make the graph less tidy and the search a bit worse. Rebuilding with `REINDEX` restores it.
- **Deletes.** Deleting a row does not remove it from the table immediately. It leaves a dead entry until Postgres runs `VACUUM`. So I check, as in task 7, that a deleted document's chunks no longer appear in search results.

All the numbers in part 2 are my estimates, not measurements. On the day I build it, I measure the build time and the index size (`\di+` in `psql`).

## Quick check
- What does `vector_cosine_ops` tell the index?
- What happens, and what is not reported, when the query operator does not match the index?
- How do I turn a cosine distance into a score for a user?
- Which setting do I change to trade speed for recall without rebuilding, and which two are fixed at build time?
