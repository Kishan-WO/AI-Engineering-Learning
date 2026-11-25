# Day 12: RAG II: retrieval, grounded generation and citations

**Build target (from the plan):** `POST /ask`, streamed, grounded answers with citations.

Today starts with the learning notes (written first, as on earlier days). The build and the results come after.

## Layout
```
day-12/
  README.md      this index
  learning/      the concept notes (written first)
  Notes/         what was built and the measured results (after the build)
```

## Learning notes (`learning/`)
They follow the plan's "Learn" sections, in order:
| Note | Plan section | What it covers |
|---|---|---|
| `1.retrieval-tuning.md` | Retrieval tuning | top-k, similarity thresholds and "nothing relevant found", MMR, removing duplicate chunks from the same section |
| `2.grounded-generation.md` | Grounded generation | prompt structure with context blocks and IDs, "answer only from the context", forcing and testing "I don't know", contradictory sources, answer language |
| `3.citations.md` | Citations | what a citation carries, inline markers mapped to sources, checking that cited IDs exist, provider-native citations |
| `4.conversational-rag.md` | Conversational RAG | rewriting a follow-up into a standalone query, when to retrieve again and when to reuse |
| `5.rag-vs-long-context-vs-fine-tuning.md` | RAG versus long context versus fine-tuning | when each is the right tool (this is also the day's required note) |

## Notes (`Notes/`)
Explanations that go with the learning notes, numbered in reading order:
| Note | Goes with | What it covers |
|---|---|---|
| `01-ask-events-and-citation-validation-explained.md` | `learning/3.citations.md`, sections 3 and 4 | the SSE events of `/ask`, the code-level check of `[n]` markers against the retrieved set, and what is and is not proved by a valid citation |

## Tasks (from the plan, not started)
| Task | What |
|---|---|
| **1** | `POST /ask`: rewrite to a standalone query (if there is history), retrieve, grounded prompt, streamed answer over SSE, a final event with citations (chunk IDs, titles, pages) |
| **2** | Check that every cited ID was in the retrieved set; strip or flag the invalid ones |
| **3** | Ask 5 questions whose answers are not in the corpus; confirm "I don't know" every time; fix the prompt until it does |
| **4** | Write 10 questions; run them against all three Day 11 chunkers; score each answer correct, partial or wrong by hand |
| **5** | Re-run the broken-table question from Day 11 and record what fixed it (structure-aware chunking, parent-child or table-as-one-chunk) |
| **6** | Save the 10 questions: they seed the golden dataset on Day 14 |
| Notes | RAG against long context against fine-tuning |

## What earlier days already give me
- **A streaming endpoint (Day 5):** `/chat` already relays an LLM stream over SSE, stores messages, and stops the upstream call when the client disconnects. `/ask` reuses that code and adds retrieval before it.
- **The `LLMClient` layer (Day 6):** retries, fallback, cost and token logging per request, and the prompt-caching habit (stable prefix first).
- **A prompt registry (Day 7):** the grounded prompt goes in `prompts/ask/v1.md`, versioned, and its version goes in the request log. Prompt changes are measured on a labelled set.
- **A router and a small model (Day 8):** the small model that classified intent can also rewrite follow-up questions cheaply.
- **Search (Day 10):** `POST /api/v1/search` returns tenant-filtered chunks with scores (checked over HTTP on 2026-11-25; the code is on branch `day-10`, not committed yet). Today's chunks are the Day 9 heading sections; their metadata is `title`, `source`, `licence`, `words` and `section_id`. **There is no page number or block type**, so a citation cannot give a page yet.
- **Ingestion (Day 11, still to be built):** the three chunkers, and the page and block-type metadata. Task 4 needs them.
- **Day 9 numbers:** the 20 labelled queries and Jina's recall@5 of 95% are the retrieval baseline. Today adds the first generation numbers.
- **Day 4 citation test:** I asked a model for citations and counted the invented ones. Today the citations come from retrieved chunks, and I check them in code.

## Points to settle at the start of the build
- **Short numbers or chunk IDs in the prompt?** The model cites `[1]`, `[2]` reliably; long IDs get mangled. I number the chunks per request and keep a map from number to chunk ID on my side.
- **How does the API signal "I don't know"?** A fixed sentence, a flag in the final event, or both. The client and the tests must be able to tell a refusal from an answer without reading prose.
- **Which similarity threshold?** I choose it from the scores of my answerable and unanswerable questions, not from a guess (note 1).
- **What does a stored golden question look like?** Question, expected answer, source document **and the text span** (not only the chunk ID): the chunk IDs change with every chunker, as Day 14 requires.
- **How do I score by hand?** A written rubric for correct, partial and wrong before I read the first answer, so that the three chunkers are scored the same way.

## What this day does not do
No re-ranker, no hybrid search, no query expansion (Day 13). No metrics beyond my hand scores (Day 14). No tracing beyond the logs (Day 15). I record the weak spots I see, and they feed those days.
