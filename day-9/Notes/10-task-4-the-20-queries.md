# Day 9 task 4: 20 real queries with the known correct document

File: `scripts/queries.json` (the first version, with the problems described below, is kept as `scripts/queries.v1.json`).

## 1. The format
Each query has `id`, `language`, `query`, `correct_docs` (a list of exact document ids from `results/documents.json`) and `notes`.

- **Rule for a hit** (decided before the final benchmark run): a result is correct when it is a section of one of the query's `correct_docs`. A hit at k means a correct section is in the top k. This is the "lenient" rule from my recall@k note.
- Every `correct_docs` id was checked against the corpus. The benchmark stops with an error if a label matches nothing.
- A query can have several correct documents when more than one page really answers it (Q2, Q4, Q6, Q9, Q10, Q11, Q15, Q16).

## 2. The 20 queries
| # | Language | Query | Correct documents | Correct sections |
|---|---|---|---|---|
| 1 | en | How do I define a path parameter in FastAPI? | `tutorial/path-params.md` | 14 |
| 2 | en | How do I validate request body fields with Pydantic? | `tutorial/body.md`, `tutorial/body-fields.md` | 10 |
| 3 | en | What is dependency injection in FastAPI? | `tutorial/dependencies/index.md` | 11 |
| 4 | en | How do I return a streaming response from a FastAPI route? | `advanced/stream-data.md`, `advanced/custom-response.md` | 22 |
| 5 | en | How do I write an async endpoint in FastAPI? | `async.md` | 19 |
| 6 | en | How do I add middleware to a FastAPI application? | `tutorial/middleware.md`, `advanced/middleware.md` | 8 |
| 7 | en | How does Pydantic handle field validation errors? | Pydantic `errors/validation_errors.md` | 97 |
| 8 | en | What is a Pydantic BaseModel and how do I use it? | Pydantic `concepts/models.md` | 27 |
| 9 | en | How do I use computed fields in Pydantic v2? | Pydantic `concepts/fields.md`, `concepts/models.md` | 47 |
| 10 | en | How do I configure Pydantic settings from environment variables? | Pydantic `pydantic_settings.md`, FastAPI `advanced/settings.md` | 14 |
| 11 | en | What is retrieval-augmented generation and why does it reduce hallucinations? | papers 2601.05264, 2504.08748 | 152 |
| 12 | en | How does the size of a text chunk affect retrieval-augmented generation? | paper 2607.24767 | 5 |
| 13 | en | What is the solubility product constant (Ksp) of silver chloride? | Chemistry Appendix J (table) | 3 |
| 14 | en | What is the standard enthalpy of formation of liquid water? | Chemistry Appendix G (table) | 9 |
| 15 | Hinglish | FastAPI mein OAuth2 password bearer kaise use karte hain? | `security/simple-oauth2.md`, `security/first-steps.md` | 17 |
| 16 | Hinglish | Pydantic model mein optional field kaise banate hain? | Pydantic `concepts/models.md`, FastAPI `tutorial/body.md` | 34 |
| 17 | Hinglish | FastAPI ke saath background tasks kaise chalate hain? | `tutorial/background-tasks.md` | 6 |
| 18 | Hinglish | Le Chatelier ka principle kya hai? | Chemistry chapter 13 | 16 |
| 19 | Hindi (Devanagari) | FastAPI में CORS कैसे enable करें? | `tutorial/cors.md` | 7 |
| 20 | en | How does Matryoshka-Adaptor produce smaller embedding dimensions? | paper 2407.20243 | 31 |

- **Mix by corpus:** 14 about FastAPI and Pydantic (Q1 to Q10 in English, Q15, Q16, Q17 and Q19 in Hindi or Hinglish), 3 about the papers (Q11, Q12, Q20) and 3 from the Chemistry book (Q13, Q14, Q18; Q13 and Q14 are answered by a table). **5 queries are Hindi or Hinglish** (Q15 to Q19), as the plan requires.
- The number of correct sections ranges from 3 (Q13) to 152 (Q11), so a query with many correct sections is easier to hit than one with few.

## 3. What was wrong with the first version, and what I changed
The first `queries.json` named a `correct_source` and a `correct_title`. The benchmark matched them by text, and **when the title was not found it counted every section of that source as correct**. That made 7 of the 20 queries almost impossible to miss (answer sets of 157 to 840 sections), so the first recall@5 of 70% and 75% was inflated.

- Q12 (embeddings) had a label for a source that is not in the corpus: it could never succeed.
- Q13 (HNSW) and Q20 (the attention mechanism) are not explained anywhere in the corpus, so they could only succeed through the fallback.
- Q14 (cosine against dot product) and Q18 (Hinglish, embedding model against chat model) had only passing mentions in one section.
- **What I did:** I checked each answer by searching the section texts for key terms (that does not use the embedding models, so the labels are not chosen to flatter a model). I replaced Q12, Q13, Q14, Q18 and Q20 with questions whose answer I found in the text (for example Appendix J has `AgCl 1.6 x 10^-10`, and Appendix G has `H2O(l) -285.83`), and switched every query to exact document ids. Q16 was kept and relabelled.
- The benchmark function `find_correct_rows` now uses `correct_docs` and has no fallback.

## 4. Limits
- 20 queries is a small set: one query is 5 percentage points.
- I wrote and labelled the queries myself, and I had seen the first benchmark results when I rewrote some of them. I kept the rule fixed before the final run, but the set is not independent of what I saw.
- The labels say which page is right, not which section. A page with many sections gives credit for any of them.

## Quick check
- Why did the old fallback inflate recall?
- Why were the new answers searched in the text and not taken from what the models returned?
- Which of the 20 queries are Hindi or Hinglish?
