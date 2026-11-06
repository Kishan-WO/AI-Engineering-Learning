# `# noqa`, linters and unused imports

Where I met it, in Alembic's `env.py`:
```python
import ai_service.db.models  # noqa: F401 (prevents linters from stripping unused model imports)
```

## 1. What a linter is
A **linter** reads my code without running it and warns about mistakes and style problems. In Python the one I use is **`ruff`** (it does the job of ESLint, and also of Prettier with `ruff format`).

```bash
uv run ruff check .          # report problems
uv run ruff check . --fix    # fix the ones it can fix safely
uv run ruff format .         # reformat
```

## 2. What `# noqa: F401` means
| Part | Meaning |
|---|---|
| `# noqa` | "no quality assurance": tell the linter **not to report a problem on this line** |
| `F401` | the **rule code** being silenced: "imported but unused" |

It is the Python version of ESLint's `// eslint-disable-next-line no-unused-vars`.

- `# noqa` alone silences **every** rule on that line. Avoid it.
- `# noqa: F401` silences **only** that rule. Prefer this.
- Several rules: `# noqa: F401, E501`.

## 3. Why this import needs it
The line only **imports** the models package. Nothing in `env.py` uses the name, so the linter says "unused import" and `--fix` would **delete it**.

But the import is needed for its **side effect**: importing the models runs the files that define `Tenant`, `User` and `Document`, which registers their tables in `Base.metadata`. Alembic's autogenerate compares `Base.metadata` with the database. Without the import, the metadata is empty and Alembic would think there are no tables.

So the comment says: "I know it looks unused. Keep it."

## 4. Rule codes
The letter shows which group of rules; the number is the rule.

| Code | Group | Example |
|---|---|---|
| `F` | Pyflakes (real mistakes) | `F401` unused import, `F841` unused variable |
| `E` | pycodestyle errors | `E501` line too long |
| `I` | isort | `I001` imports not sorted |
| `UP` | pyupgrade | `UP017` use `datetime.UTC` |
| `B` | bugbear | `B006` mutable default argument |

Look a rule up: `uv run ruff rule F401` explains it.

The rules switched on for a project live in `pyproject.toml`:
```toml
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

## 5. Other ways to say "this is fine"
| Way | Use |
|---|---|
| `# noqa: F401` on the line | One exception |
| `__all__ = [...]` listing a re-exported name | Marks an import as intentionally public (no `noqa` needed) |
| `per-file-ignores` in `pyproject.toml` | A whole file is exempt from a rule |
| Using the name for real | Best, when possible |

## Common mistakes
| Mistake | What happens |
|---|---|
| Plain `# noqa` everywhere | Hides real problems on that line too |
| Deleting an import because the linter calls it unused | Side-effect imports (models, plugins) stop working |
| Running `--fix` without reading the result | It may remove such imports if they lack `noqa` |
| Wrong code in `# noqa: Fxxx` | The real rule still reports |

## Quick check
- What do `noqa` and `F401` each mean?
- Why must the models import stay even though the code never uses it?
- Why is `# noqa: F401` better than plain `# noqa`?
- Which two ways keep an unused-looking import from being flagged?
