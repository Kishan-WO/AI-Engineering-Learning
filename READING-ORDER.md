# Reading order: what was done each day, and in which order to read it

This repository holds my learning notes, the practice code and the measured results of the course, one folder per day. The service itself (`ai-service`, Days 3 to 8) is in a separate repository: Days 5 to 8 here hold the concept notes and the result notes, and the code is in `ai-service` on the branch `day-N`.

Every day folder follows the same shape, so a day can be read the same way each time:
1. `README.md`: the build target, the tasks and what each one gave.
2. `learning/`: the concept notes, in the order of the plan. They were written before the build.
3. `tasks/` (or `docstore/`, `scripts/`): the code of the day, where it lives in this repository.
4. `Notes/`: what was built, with the real numbers, and the explanations.
5. `results/`: the saved outputs of runs (some days).

## Day 1: Python fundamentals (`day-1/`)
Read in this order: `README.md`; `learning/` (`modules-packages-and-all.md`, `star-and-double-star-unpacking.md`, `keyword-only-arguments.md`, `mixins-and-multiple-inheritance.md`, then the others); `tasks/task1_exercises.py`, `task2_chunk_words.py`, `task3_save_docs.py` and the `tasks/docstore/` package; `tasks/task4_bugs.py`; then `Notes/` (`task-2-chunk-words-sliding-window.md`, `task-3-docstore-walkthrough.md`, `task-4-mutable-default-argument-explained.md`, `task-5-python-vs-javascript.md`).

## Day 2: typing, asyncio, a UV project (`day-2/`)
Read in this order: `README.md`; `learning/1.iterable-vs-iterator.md` to `12.blocking-loop-to-thread-httpx.md` (in number order); the `docstore/` project (`src/docstore/`, then its `tests/`); the task scripts in `tasks/`; then `Notes/` (retry decorator, timer context manager, the `docstore` UV project and CLI, field and model validators, the async fetcher walkthrough).

## Day 3: the base service (in `ai-service`, branch `day-3`)
No code here. In the `ai-service` repository: `git switch day-3` and read its `READING-ORDER.md`.

## Day 4: LLM fundamentals (`day-4/`)
Read in this order: `README.md`; `learning/1.how-an-llm-works.md` to `8.local-models.md`; the code in `tasks/` (`llm_client.py` first, then `task1_token_counts.py` to `task7_citations.py`); the saved outputs in `results/`; then `Notes/task-1-...` to `task-7-citations-hallucination-test.md`, which have the measurements (token cost of English, Hindi and Hinglish, temperature runs, latency, the citation test).

## Day 5: messages, streaming, structured output (`day-5/`)
Read in this order: `README.md`; `learning/` (`1.messages-api.md`, `2.streaming.md`, `3.structured-output.md`); then `Notes/tasks-1-5-chat-and-extract.md` for what was built and measured. The code is in `ai-service`, branch `day-5` (`READING-ORDER.md` there).

## Day 6: reliability, cost, provider abstraction (`day-6/`)
Read in this order: `README.md`; `learning/` (`1.error-handling.md`, `2.token-accounting-and-cost.md`, `3.prompt-caching.md`, `4.provider-abstraction.md`); then `Notes/tasks-1-7-reliability-cost-providers.md`. The code is in `ai-service`, branch `day-6`.

## Day 7: prompt engineering (`day-7/`)
Read in this order: `README.md`; `learning/` (`1.prompt-anatomy.md` to `6.measuring-prompts.md`); then `Notes/tasks-1-6-prompt-registry-and-measured-prompts.md`. The code is in `ai-service`, branch `day-7`.

## Day 8: LLM orchestration (`day-8/`)
Read in this order: `README.md`; `learning/` (`1.chains.md` to `5.framework-trade-offs.md`); then the task notes in `Notes/` (the router and its accuracy, cost and latency against always-large, the parallel summarise chain, the LangGraph router and the framework comparison). The code is in `ai-service`, branch `day-8`.

## Day 9: embeddings (`day-9/`), code and results are in this repository
Read in this order:
1. `README.md` (the tasks and the status of each).
2. `learning/1.numpy-essentials.md` to `7.use-cases.md` (note 3 has the unit-vector picture).
3. `corpus/README.md` and `corpus/manifest.json`: the corpus, its sources and licences (the downloaded files are not in git; `corpus/download_corpus.py` rebuilds them).
4. `Notes/` in number order: `01` (the RAG picture) to `15`. The task notes are `03` (load the corpus), `05` (embed), `08` (NumPy search), `10` (the 20 queries), `12` (the Jina against BGE-M3 benchmark), `13` (queries where both fail) and `14` (near-duplicates).
5. `scripts/` in task order: `load_corpus.py`, `embed_jina.py`, `search.py`, `queries.json`, `benchmark.py`, `detect_near_duplicates.py`.
6. `results/`: `benchmark_results.json`, `near_duplicates_jina_0.97.json`, the two `*_meta.json` files, `search_examples.txt`, and `sample_vector/` (one real vector in four formats, with their sizes).

## How to run the code of a day
Days 1, 2, 4 and 9 each have a `pyproject.toml`: in that day's folder run `uv sync`, then run the scripts with `.venv/Scripts/python script.py` (Windows). API keys go in a `.env` file in the day's folder (copy `.env.example`); `.env` is ignored by git.
