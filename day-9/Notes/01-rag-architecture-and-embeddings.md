# RAG architecture: how embedding vectors are used by a chat model (LLM)

This note answers three questions I asked on Day 9:
1. How do the vectors made by an embedding model reach a chat model (an LLM)?
2. What is the full architecture of a RAG system?
3. Can I use the vectors with any model? What if two models have different embeddings?

## 1. The one-sentence answer
**The chat model never sees the vectors.** The vectors are only used to **find text**. The chat model receives that **text**, as words in its prompt, and writes the answer from it.

```
vectors  ->  find the right pieces of text  ->  paste the text into the prompt  ->  the chat model reads the text
```

Embeddings are the search engine of the system. The chat model is the writer.

## 2. The full picture: two phases
RAG (retrieval-augmented generation) has an **offline** phase, done once per document, and an **online** phase, done for every question.

```
OFFLINE (ingestion): done when a document is added
  document ──> parse ──> split into chunks ──> EMBEDDING MODEL ──> vectors ──┐
                                   │                                          ├──> vector store
                                   └── the chunk text, source, title ─────────┘     (vector + text + metadata)

ONLINE (every question)
  question ──> EMBEDDING MODEL (the same one) ──> query vector
                                                      │
                                    search the vector store: top-k nearest chunks
                                                      │
                                       (optional) re-rank, filter by tenant or source
                                                      │
                          build the prompt: instructions + the chunk TEXTS + the question
                                                      │
                                              CHAT MODEL (LLM) writes the answer
                                                      │
                                   answer + citations (which chunks it used)
```

## 3. One question, step by step
The question and the texts below are placeholders. They only show the order of the steps.

1. **Embed the question** with the same embedding model that embedded the corpus, in its *query* mode. Result: one vector (for example 1,024 numbers).
2. **Search.** Compare it with all the stored vectors (normalise, `docs @ q`, top-k with `argpartition`, as in my NumPy `search`). The top k rows come back with their scores.
3. **Look up the text.** The search gives row numbers. The vector file has no words in it, so each row number is used to read that section's text from the metadata file (row 812 means "section number 812, with its title, source and text").
4. **Build the prompt.** The chat model gets plain text, for example:
   ```
   Answer only from the context. If the answer is not in the context, say so.
   Cite the source ids.

   [S1] <source and heading of the first retrieved section>
   <the text of that section>
   [S2] <source and heading of the second retrieved section>
   <the text of that section>

   Question: <the user's question>
   ```
5. **The chat model answers** from that text and cites `[S1]` and `[S2]`. The service turns the ids into links to the sources.

The vectors did their job in step 2 and were not used again.

## 4. The parts of the architecture, and where I build them
| Part | What it does | Where in the course |
|---|---|---|
| Parser | turns a PDF or HTML file into clean text | Day 11 |
| Chunker | cuts text into pieces that make sense alone | Day 9 (by heading, for now), Day 11 |
| **Embedding model** | text to a vector | Day 9 |
| Vector store | keeps vectors, text and metadata; finds the nearest | Day 9 NumPy, Day 10 pgvector and Qdrant |
| Retriever | embeds the question, takes the top-k, applies filters such as tenant | Day 10, 12 |
| Keyword search and fusion | BM25 plus vectors, merged | Day 13 |
| Re-ranker | reads the question and each candidate together and re-orders them | Day 13 |
| Prompt builder | instructions, chunk texts with ids, the question | Day 12 |
| **Chat model (LLM)** | writes the answer from the text it was given | Day 12 |
| Citations and guardrails | which source said it, and "I don't know" when nothing relevant was found | Day 12 |
| Evaluation | is the right chunk found, and is the answer faithful to it | Day 14 |

## 5. Three different things are called "embedding"
| Name | What it is | Do I use it? |
|---|---|---|
| **Token embeddings inside a chat model** | the first layer of the chat model turns each token into numbers so it can compute | No. It is internal and the model never gives these out. |
| **Text embedding model vectors** | a separate model whose whole job is "text in, one vector out" | **Yes.** This is what I store and search. |
| The chat model's hidden states | numbers inside the model while it is thinking | No. |

So "the chat model's embeddings" and "the embedding model's vectors" are not the same thing, and I cannot ask a chat model to read my vector file. A chat model takes text.

## 6. The rule: a vector can only be compared with vectors from the same model
Every embedding model builds its own space. The same sentence gets different numbers from each model, and the numbers mean different things.

- **Same model for documents and queries.** The query vector must come from the model that made the stored vectors. Not "the same provider": the same model and version.
- **Same settings too.** The same number of dimensions (if I truncated, truncate the query the same way and normalise it), the same input type (document mode when storing, query mode when searching), the same normalisation.
- **Two models with the same length do not match either.** A 1,024-number vector from Jina and a 1,024-number vector from BGE-M3 are unrelated. Their cosine similarity is about as meaningful as comparing two random lists. (I can check that on my own corpus later: embed one text with both models and compute the cosine between the two vectors. I have not run this yet.)
- **A different length cannot even be compared**: 3,072 numbers against 1,024 will not multiply.
- Think of it as two maps with different coordinates: a place has coordinates on each map, but the numbers on one map say nothing on the other.

### What this means in practice
| If I change... | Do I need to embed the documents again? |
|---|---|
| the chat model (GPT, Claude, Gemini, a local one) | **No.** It only reads text. |
| the re-ranker | **No.** It also works on text. |
| the vector store (NumPy, pgvector, Qdrant) | **No**, only the stored vectors are copied over (the length must fit the table). |
| the embedding model | **Yes, all of them.** The old vectors and the new query vectors do not match. |
| the chunking | **Yes**, the pieces are different. |
| the number of dimensions (truncating) | The stored vectors must be truncated and normalised the same way, and so must every query. |

### So how do I know which model made the vectors?
Nothing in the vectors says so. I store it next to them: the model name and version, the dimensions, the input type, whether they were normalised, the date. If that is missing, a vector file is not usable later.

The vector file has to be searched with a query that the **same embedding model** makes, so the system always needs that embedding model available when it answers a question: its API key and limits, or the local weights.

## 7. Two different chat models, two different embedding models
- **Chat model A and chat model B are independent of the embeddings.** I can answer from the same retrieved text with either, or both, and compare them. The cost and quality of the answer change, not the search.
- **Embedding model X and embedding model Y are independent of each other.** Each needs its own vectors of the whole corpus. That is what the Day 9 benchmark does: one vector file per model, the same 20 queries, and the recall@5 of each.
- **A provider's chat model and its embedding model are separate products.** Choosing a Gemini chat model does not force Gemini embeddings, and Jina embeddings do not force any chat model.

## 8. What goes wrong, and where
RAG fails in three places, and each needs a different fix:
| Failure | Example | Fix |
|---|---|---|
| **Retrieval:** the right chunk is not in the top-k | the question uses different words, or the chunk was cut badly | better embedding model, chunking, hybrid search, re-ranking |
| **Context:** the right chunk was found but does not contain the whole answer | the answer needs the paragraph before it | bigger or overlapping chunks, add the title and heading to the chunk |
| **Generation:** the chat model had the right text and still answered wrongly | it ignored the context or made things up | better prompt, "answer only from the context", a citation check |

Day 14 measures retrieval and generation separately for this reason: one score for "the whole RAG" does not say which part to fix.

## 9. Cost and time of one question
| Step | Rough size | Who is paid |
|---|---|---|
| Embed the question | milliseconds to a second, a few tokens | the embedding model |
| Search the vectors | milliseconds for thousands of vectors (NumPy) | nobody (my own CPU) |
| Re-rank (optional) | hundreds of milliseconds | the re-ranker |
| Write the answer | seconds, and the most tokens: the question plus every chunk plus the answer | the chat model |

Most of the cost of a question is the chat model reading the chunks, so top-k trades quality against money: too small and the evidence is missed, too big and the prompt gets long and noisy.

## 10. What I will check myself on Day 9
- The search step (steps 1 to 3 above) with my own NumPy `search`, before any chat model is involved.
- Which of my test queries find the right section with each embedding model.
- That I record the model name, dimensions and input types next to every vector file.

## Quick check
- Does the chat model receive vectors? What does it receive?
- Why can I swap the chat model without re-embedding, but not the embedding model?
- Why is a 1,024-number vector from one model useless against a 1,024-number vector from another?
- What must be stored next to a vector file so it can be used later?
- Name the three places a RAG answer can go wrong.
