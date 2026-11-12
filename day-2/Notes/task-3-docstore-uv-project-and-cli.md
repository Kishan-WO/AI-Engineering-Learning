# Docstore as a `uv` project, what changed from Day 1, and the CLI

Question: turn docstore into a uv project, what did you change from Day 1, and how do I run the CLI commands?

Location: `day-2/docstore/`.

## 1. The layout
```
day-2/docstore/
  pyproject.toml      dependencies, [project.scripts], pytest / mypy / ruff settings
  uv.lock
  README.md
  src/docstore/       __init__, exceptions, models, storage, store, loader, cli, py.typed
  tests/              conftest + 5 test files, and data/sample_docs (the 50 files)
```
- **`src/` layout**: the package is in `src/docstore/`, not at the project root, so tests import the *installed* package, as a user would (see `task-3-import-name-vs-package-name.md`).
- **`py.typed`**: an empty marker file that tells type checkers "this package has type hints".
- **`[project.scripts]`**: `docstore = "docstore.cli:app"` creates a command called `docstore`.

## 2. What changed from the Day 1 version
The **logic is the same**. The changes are style and packaging.

| Area | Change | Why |
|---|---|---|
| `models.py` | `datetime.now(timezone.utc)` → `datetime.now(UTC)` | Ruff rule `UP017`: Python 3.11+ has `datetime.UTC` |
| `storage.py` | `elif` after a `return` → `if`; `get`/`all` shortened | Ruff `RET505` and a simpler body |
| imports | Sorted; `import x` lines first | Ruff `I` (isort) |
| `__init__.py` | `__all__` sorted | Ruff `RUF022` |
| `loader.py` | One generator expression on one line | `ruff format` |
| New `cli.py` | A `typer` command-line interface | Use the library from the terminal |
| Tests | One `assert` script → 42 `pytest` tests | `tmp_path`, `parametrize`, `pytest.raises`, `monkeypatch`, `caplog`, `CliRunner` |
| Checks | `mypy --strict`, `ruff`, coverage minimum 85% in `pyproject.toml` | Quality gates; coverage is 100% |
| Packaging | Own `pyproject.toml`, `uv.lock`, `.venv` | See `task-3-uv-projects-and-virtual-environments.md` |

## 3. The CLI commands
From `day-2/docstore`:
```bash
uv run docstore --help
uv run docstore load tests/data/sample_docs    # creates docs.json in the current folder
uv run docstore count
uv run docstore list --limit 5
uv run docstore search monsoon
uv run docstore get <id>
uv run docstore delete <id>
```
- The data file is `docs.json` in the **current folder**, or `--store path.json`, or the `DOCSTORE_PATH` environment variable. Running from different folders looks like "the data vanished".
- `load` skips files already loaded, so a second run says `Added 0 documents`.
- Errors print `Error: ...` to stderr with exit code 1; a missing folder is a usage error (exit code 2). No tracebacks.

## 4. How `typer` works
```python
app = typer.Typer(help="A small document store.", no_args_is_help=True)

@app.command()
def load(folder: Annotated[Path, typer.Argument(exists=True, file_okay=False)],
         store: StoreOption = Path("docs.json")) -> None: ...
```
- A function with type hints becomes a command; parameters become arguments and options.
- `Annotated[Path, typer.Argument(exists=True, ...)]` makes typer check the folder exists.
- `typer.Exit(code=1)` ends the program with a status code.
- Testing uses `typer.testing.CliRunner` instead of starting a process.

## 5. Install as a command anywhere
```bash
uv tool install --editable .
docstore count
```
`--editable` uses the source as it is, so edits apply immediately.

## 6. Quality commands
```bash
uv run pytest        # 42 tests; fails below 85% coverage
uv run mypy          # strict type check
uv run ruff check .  # lint
uv run ruff format --check .
```

## Quick check
- Why does the `src/` layout stop me importing code by accident?
- What creates the `docstore` command?
- Where does the data file end up, and how can I choose another one?
- Which Day 1 files changed in logic, and which only in style?
