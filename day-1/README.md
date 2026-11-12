# Day 1: Python core language for JavaScript developers

Everything here belongs to one task or to the learning part. Run every command from this folder (`day-1`).

## Layout
```
day-1/
  README.md          this index
  pyproject.toml     uv project (no packages: standard library only)
  learning/          concept notes (one topic each)
  tasks/             the code, named task1_ ... task4_
    docstore/        the package built in task 3
  data/              input files (the 50 sample documents)
  results/           output of the tasks (docs.json)
  Notes/             one note per task, named task-N-...
```

## Tasks
| Task | What | Code (`tasks/`) | Data and output | Note (`Notes/`) |
|---|---|---|---|---|
| **1** | 15 short exercises (strings, collections, comprehensions, match) with docstrings | `task1_exercises.py` | | |
| **2** | `chunk_words(text, size, overlap)`: overlapping word windows and their edge cases | `task2_chunk_words.py` | | `task-2-chunk-words-sliding-window.md` |
| **3** | The `docstore` package: Document dataclass, abstract Storage, JSON and in-memory storage, loader, custom errors | `docstore/` (package), `task3_test_docstore.py`, `task3_save_docs.py` | `data/sample_docs/` (50 files), `results/docs.json` | `task-3-docstore-walkthrough.md` |
| **4** | Reproduce the mutable-default and shallow-copy bugs, then fix them | `task4_bugs.py` | | `task-4-mutable-default-argument-explained.md` |
| **5** | "Python vs JavaScript" note | | | `task-5-python-vs-javascript.md` |

## Concept notes (`learning/`)
| Note | Topic |
|---|---|
| `keyword-only-arguments.md` | The `*` and `/` in a function definition |
| `star-and-double-star-unpacking.md` | `*` and `**` collecting and unpacking |
| `lru-cache-and-singleton.md` | `functools.lru_cache` and the cached settings object |
| `mixins-and-multiple-inheritance.md` | Mixins, multiple inheritance, MRO |
| `bytes-and-bytesio.md` | `str` vs `bytes`, `io.BytesIO` |
| `modules-packages-and-all.md` | Modules, packages, `__init__.py`, `__all__` |
| `closures-nonlocal-and-finally.md` | Closures, `nonlocal`, `try/finally` |

## How to run
```bash
uv run python tasks/task1_exercises.py
uv run python tasks/task2_chunk_words.py       # runs its own checks
uv run python tasks/task3_test_docstore.py     # prints "all docstore tests passed"
uv run python tasks/task3_save_docs.py         # loads data/sample_docs into results/docs.json and searches it
uv run python tasks/task4_bugs.py
```
