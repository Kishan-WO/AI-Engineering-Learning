# Vector Databases

A vector database stores embeddings and finds the nearest neighbours of a query vector quickly.

Exact search compares the query with every vector, which is slow for large collections. Approximate nearest neighbour indexes, such as HNSW, trade a little accuracy for much faster search.

Popular options include pgvector, Qdrant, Pinecone and Weaviate. Always filter by tenant inside the query so users never see each other's data.
