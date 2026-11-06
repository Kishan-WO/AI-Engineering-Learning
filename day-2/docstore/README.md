# docstore

A small typed document store: in-memory and JSON backends, a folder loader and a CLI.

## Setup
```bash
uv sync
```

## CLI
```bash
uv run docstore load tests/data/sample_docs   # creates docs.json in the current folder
uv run docstore list --limit 5
uv run docstore search monsoon
uv run docstore get <id>
uv run docstore delete <id>
uv run docstore count
```
Use `--store path.json` (or `$DOCSTORE_PATH`) to pick another file.

## Checks
```bash
uv run pytest            # 85% minimum coverage is enforced
uv run mypy              # strict
uv run ruff check .
uv run ruff format --check .
```
