# `uv` projects and virtual environments: one per day

Question: stop installing packages globally; give each day its own environment. And: why did `uv init` quietly create a workspace?

## 1. The npm comparison
| Node | Python with uv |
|---|---|
| `package.json` | `pyproject.toml` |
| `package-lock.json` | `uv.lock` |
| `node_modules/` | `.venv/` |
| `npm install` | `uv sync` |
| `npm install pkg` | `uv add pkg` |
| `npm install -D pkg` | `uv add --dev pkg` |
| `npx` / `npm run` | `uv run` |

A **virtual environment** (`.venv`) is a private folder with its own Python and its own installed packages. It keeps one project's packages from mixing with another's or with the system Python.

## 2. What I do now
Each day is its own project, with its own `pyproject.toml`, `uv.lock` and `.venv`:
```
day-1/          stdlib only
day-2/          pydantic, httpx, python-dotenv; dev: pytest, mypy, ruff ...
day-2/docstore/ its own project
ai-service/     the Day 3 service
```
Commands, always from inside the project folder:
```bash
uv init --bare --name day-2 --python 3.14   # create pyproject.toml only
uv add pydantic httpx python-dotenv         # add packages (edits pyproject.toml and uv.lock, installs)
uv add --dev pytest ruff mypy               # development-only packages
uv sync                                     # (re)build .venv from the lock file
uv run python timing.py                     # run inside the project's environment
```
`uv run` finds the project's `.venv` itself; no activation needed.

## 3. What each file is
| File | Role |
|---|---|
| `pyproject.toml` | Name, Python version, dependencies, tool settings |
| `uv.lock` | The exact versions installed. Commit it |
| `.venv/` | The installed packages. **Never commit it**; it can be rebuilt any time |
| `.python-version` | Which Python version the project uses |

In `pyproject.toml`, `dependencies` are needed to run the project and `[dependency-groups] dev` are only for development (tests, linters).

## 4. The workspace surprise
When I ran `uv init` inside a folder whose parent already had a `pyproject.toml`, uv printed:
```
Adding `docstore` as member of workspace `C:\Projects\ai-eng`
```
and wrote this into the **parent's** `pyproject.toml`:
```toml
[tool.uv.workspace]
members = ["day-2/docstore"]
```
A **workspace** is a group of projects that share one `uv.lock` and one `.venv` at the top. That is not what I wanted: the packages were global again, and a Docker build could not find `uv.lock` inside the project folder.

Fix: delete the parent `pyproject.toml`, `uv.lock` and `.venv`, then run `uv sync` inside each project. Each now has its own lock and environment. Rule: **do not keep a `pyproject.toml` in a folder above other projects, unless a workspace is the goal.**

## 5. A moved `.venv` breaks
A virtual environment stores **absolute paths** (to its Python and its scripts). If the folder is moved or renamed, the old `.venv` points to places that no longer exist. Delete it and run `uv sync`; it is rebuilt in seconds from the lock file.

## 6. `uv init` also does other things
- `uv init --lib` creates the `src/` layout and a `py.typed` file; plain `uv init` creates a script project; `--bare` creates only `pyproject.toml`.
- It may run `git init` and write a `.gitignore` inside the folder. An empty repository nested inside another is a nuisance; remove it if it is not wanted.
- It reads the author from the machine's git configuration.

## Common mistakes
| Mistake | What happens |
|---|---|
| `pip install` into the system Python | Global mess; versions clash between projects |
| Committing `.venv` | A huge, machine-specific folder in git |
| Not committing `uv.lock` | Different machines install different versions |
| Moving a project folder and keeping its `.venv` | Broken scripts; rebuild with `uv sync` |
| A `pyproject.toml` in a parent folder | `uv init` may turn the children into workspace members |
| Running `python` instead of `uv run python` | Uses the wrong environment, so `ModuleNotFoundError` |

## Quick check
- What are the Python equivalents of `package.json`, `package-lock.json` and `node_modules`?
- What does `uv run` do that plain `python` does not?
- What is a uv workspace, and why did it get in my way?
- Why must a `.venv` be rebuilt after the folder moves?
