# PostgreSQL Indexes

An index speeds up lookups at the cost of extra storage and slower writes.

The default index type is a B-tree, which supports equality and range queries. GIN indexes are used for full-text search and JSONB, and HNSW indexes from the pgvector extension are used for vector similarity search.

Use `EXPLAIN ANALYZE` to check whether a query actually uses an index.
