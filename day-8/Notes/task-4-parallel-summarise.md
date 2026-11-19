# Day 8 task 4: summarise 10 documents in parallel, then combine

Built in `ai-service/src/ai_service/services/summarise_service.py`, with the prompts `summarise_document` v1 and `combine_summaries` v1, tests in `tests/test_summarise.py` and a live run in `scripts/run_summarise_demo.py` (results in `scripts/results/summarise_demo.json`). Decisions 56 to 59 are in `decisions.md`.

## 1. The chain
```
doc 1 -> summary 1 -+
...                 +--> combine (one call) --> overview
doc 10 -> summary 10 -+
   MAP: parallel, at most `concurrency` calls at once        REDUCE: one call
```
`summarise_documents(docs, client, concurrency=4, max_failures=2, retry_failed=True, timeout=60)`.

## 2. How the three required parts work
| Part | How |
|---|---|
| **Parallel** | `asyncio.gather` over one `_summarise_one` coroutine per document; the results come back in the input order |
| **Concurrency limit** | an `asyncio.Semaphore(concurrency)` around each call; a counter records the highest number of calls running at the same moment (`peak_in_flight`), so the limit is measured, not assumed |
| **One deliberately failing call** | the script wraps the client so the call for document `d7` always raises `OverloadedError` (no model call is made for it); the tests do the same with a fake client, and also make a call fail once and then work |

## 3. The failure policy (written down, not left to chance)
1. `gather(..., return_exceptions=True)`: one failed call does not throw away the other nine summaries.
2. **Retry the failed documents once** (a second map pass on only those).
3. **Still failing:** continue without them if there are at most `max_failures` (2). The result lists each failed document (id, error kind, attempts), and the combine prompt is told "this covers only 9 of 10 documents (failed: d7)", so the overview says so at its start.
4. **More than `max_failures` failed** (or none worked): stop with `TooManyFailuresError` before the combine call, because an overview built on too little would mislead.
5. A **timeout** per call (`asyncio.timeout`): a stuck call counts as a failed document.
6. A failure of the combine call is a clean `LLMUnavailableError` (the API turns it into a 502). A bug (any exception that is not a model error) is raised, not hidden as a "failed document".

## 4. Measured (real model, one run each, `gemini-3.1-flash-lite`, 10 handbook sections, 10,696 characters)
| Run | Concurrency | Wall time | Map step | Combine | Calls | Peak in flight | Coverage | Cost |
|---|---|---|---|---|---|---|---|---|
| A sequential | 1 | 25.74 s | 22.58 s | 3.15 s | 11 | 1 | all 10 | $0.003357 |
| B parallel | 4 | 10.24 s | 8.14 s | 2.10 s | 11 | 4 | all 10 | $0.003576 |
| C parallel, d7 fails | 4 | 5.31 s | 3.81 s | 1.51 s | 12 (10 reached the model) | 4 | 9 of 10 (failed: d7) | $0.003283 |

- **Parallel is 2.5 times faster on wall time** (25.74 s to 10.24 s) and 2.8 times on the map step, for about the same cost. It is not 4 times faster because ten documents with a limit of four run in three waves (4, 4, 2), and the combine call (2 to 3 s) cannot start before the last summary.
- **The limit held:** peak in flight was 1, 4 and 4.
- **Run C** made 12 calls: nine summaries that worked, `d7` twice (the original and the one retry, both failed with `OverloadedError`), and the combine call. The result said `9 of 10 documents (failed: d7)` and the overview began "This overview covers only 9 of 10 documents (failed: d7)". The refund policy section is `d7`, and the refund details are indeed missing from that overview, as they are present in B.
- **Run C was faster than B although it did the same work minus one call.** That is the variance of the provider's response time (one run each), not an effect of the failure. The difference between A and B is large enough to trust; differences of a few seconds between B and C are not.

## 5. The API route: `POST /summarise`
- Body: `document_ids` (1 to 20 of my own stored documents, no duplicates), `backend`, `concurrency` (1 to 8, default 4). The text is read from the database, so nothing large travels in the request and another tenant's id is a 404.
- A document over 30,000 characters is refused (413) before any model call, because cutting it silently would summarise something else.
- Answer: `overview`, `summaries`, `failed` (document, error kind, attempts) and `meta` (coverage text, model calls, peak in flight, map and combine seconds, tokens). More than 2 failed documents is a 502 that names them.
- Seven tests (`tests/test_summarise_api.py`): success, one failing document, too many failing, a foreign tenant's document, the size limit, request validation, login.

## 6. What this does not show
- **One run per setting and one concurrency value (4).** I did not try 2, 8 or 10, so I do not know where the curve flattens.
- **Quality of the overview is not scored.** I read it for the failure case only; there is no rubric as in task 3.
- The reduce step is **one call**. With many documents the summaries would not fit the context window; the fix is to combine in groups first (the learning note describes it), which I did not build.
- The route is a plain request-response call (5 to 10 s for ten documents); a background job with polling was not built.

## Quick check
- Why `return_exceptions=True`, and what would the default `gather` have done to the other nine summaries?
- Why is the speed-up 2.5 times and not 4 times?
- What does the combine prompt say when a document failed, and why?
- When does the chain stop instead of continuing without the failed documents?
