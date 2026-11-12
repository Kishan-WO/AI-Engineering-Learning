# Day 2: Pythonic features, typing, tooling and asyncio

Everything here belongs to one task or to the learning part. Run every command from this folder (`day-2`).

## Layout
```
day-2/
  README.md          this index
  .env, .env.example private settings (WIKI_CONTACT); .env is not committed
  pyproject.toml     uv project (pydantic, httpx, python-dotenv; dev: pytest, mypy, ruff)
  learning/          the 12 numbered learning notes (what was taught, topic by topic)
  tasks/             the code, named task1_ ... task5_
  data/              input and cache files (titles.json)
  Notes/             one note per task, named task-N-...
  docstore/          task 3: docstore as its own uv project (src layout, CLI, tests)
```

## Tasks
| Task | What | Code | Note (`Notes/`) |
|---|---|---|---|
| **1** | `@retry` with exponential backoff and jitter, sync and async | `tasks/task1_retry.py` | `task-1-retry-decorator-explained.md` |
| **2** | `@timed` decorator and a `timer()` context manager | `tasks/task2_timing.py` | `task-2-timer-context-manager.md`, `task-2-paramspec-and-double-star.md` |
| **3** | docstore as a `uv` project: `src/` layout, typer CLI, 42 tests, `mypy --strict`, `ruff` | `docstore/` (own project) | `task-3-docstore-uv-project-and-cli.md`, `task-3-uv-projects-and-virtual-environments.md`, `task-3-noqa-and-linters.md`, `task-3-import-name-vs-package-name.md`, `task-3-type-checker-messages-and-fixes.md` |
| **4** | Pydantic model for a messy student enquiry; validate 30 messy rows | `tasks/task4_enquiry.py` | `task-4-field-validator-vs-model-validator.md` |
| **5** | Async fetcher: 100+ Wikipedia pages, sequential vs threads vs asyncio, semaphore, retries | `tasks/task5_fetcher.py` (uses `task1_retry.py`), cache `data/titles.json` | `task-5-fetcher-walkthrough.md`, `task-5-dotenv-and-environment-variables.md` |
| **6** | `time.sleep(1)` inside the async fetch: observe, fix, explain | not done | |
| **7** | Tests with `pytest-asyncio` and `respx`: a 429 is retried, a 404 is not | not done | |

## Learning notes (`learning/`)
| Note | Topic |
|---|---|
| `1.iterable-vs-iterator.md` | Iterable vs iterator |
| `2.itertools.md` | `chain`, `islice`, `groupby`, `batched` |
| `3.yield-and-yield-from.md` | Generators |
| `4.decorators.md` | Decorators, `functools.wraps`, decorators with arguments |
| `5.context-managers.md` | `contextlib.contextmanager` |
| `6.type-hints.md` | Type hints, `Protocol`, generics |
| `7.pydantic.md` | Pydantic v2 |
| `8.io-cpu-gil-concurrent-futures.md` | I/O vs CPU bound, the GIL, threads and processes |
| `9.asyncio-vs-node-event-loop.md` | asyncio vs the Node event loop |
| `10.tasks-taskgroup-semaphore-timeout-cancel.md` | Tasks, `gather`, `TaskGroup`, `Semaphore`, timeout, cancellation |
| `11.async-generators.md` | Async generators |
| `12.blocking-loop-to-thread-httpx.md` | Blocking the loop, `to_thread`, `httpx` |

## How to run
```bash
uv run python tasks/task1_retry.py          # prints each test and "all retry tests passed"
uv run python tasks/task2_timing.py
uv run python tasks/task4_enquiry.py        # validates the 30 rows and prints the report
uv run python tasks/task5_fetcher.py        # needs WIKI_CONTACT in .env; makes about 360 requests to Wikipedia

cd docstore
uv run pytest                               # task 3: 42 tests, coverage 85% minimum
uv run docstore --help
```

## Setup
- `uv sync` installs the packages (the `docstore` folder has its own `uv sync`).
- Task 5 needs `WIKI_CONTACT=` (an email or a profile URL) in `day-2/.env`; `.env` is git-ignored.
