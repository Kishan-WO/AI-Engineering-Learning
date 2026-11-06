# Retrieval-Augmented Generation

Retrieval-augmented generation (RAG) gives an LLM relevant documents at query time so it can answer questions about data it was not trained on.

## The pipeline
1. Split documents into chunks.
2. Embed each chunk and store it in a vector database.
3. At query time, embed the question and retrieve the most similar chunks.
4. Put the chunks in the prompt and ask the model to answer only from them, with citations.
