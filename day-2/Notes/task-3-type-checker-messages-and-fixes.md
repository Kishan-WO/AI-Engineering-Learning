# Type-checker and linter messages I hit, and what they meant

A short field guide to the editor messages I asked about. Each is a warning from a tool (pyright, mypy or ruff), not a Python crash: the code still ran.

## 1. "`t2` is possibly unbound" / "uninitialized"
```python
try:
    with timer("failing block") as t2:
        raise RuntimeError("oops")
except RuntimeError:
    print(t2.elapsed)        # warning
```
`t2` only gets a value after `timer(...)` is created **and** `__enter__` returns. The checker cannot prove that, because an exception could occur before the assignment.

Fix: create the object **before** the `try`:
```python
t2 = timer("failing block")
try:
    with t2:
        raise RuntimeError("oops")
except RuntimeError:
    print(t2.elapsed)        # always defined
```
General rule: a name first assigned inside `try`, `if` or `with ... as` may not exist later. Give it a value first, or restructure.

## 2. "Cannot find type stubs for module `retry` ... install `types-retry`"
My file was called `retry.py`. A well-known library on PyPI is also called `retry`, and it has a stub package `types-retry`. The checker matched my import to that library.

Fix: rename my module to something unique (`task1_retry.py`). Do **not** install `types-retry`.

Rule: never name my own module like a real library (`retry`, `json`, `types`, `email`, `test`, `requests`). Python or a tool may import the wrong one. (More: `task-3-import-name-vs-package-name.md`.)

## 3. "Call to deprecated overload `contextlib.asynccontextmanager`"
```python
@asynccontextmanager
async def lifespan(app) -> AsyncIterator[None]:     # deprecated annotation
```
`@asynccontextmanager` wraps a generator function, so the honest return type is the generator:
```python
from collections.abc import AsyncGenerator

@asynccontextmanager
async def lifespan(app) -> AsyncGenerator[None]:
```

## 4. `task4_bugs.py` had many errors
| Message | Cause | Fix |
|---|---|---|
| "Object of type None is not subscriptable" on `add_tag_buggy.__defaults__[0]` | A function's `__defaults__` is `None` when it has no defaults | `defaults_tuple: tuple[Any, ...] = f.__defaults__ or ()` |
| `Collection[str]` has no `append`; not indexable (9 errors) | A dict with mixed values (str, dict, list) was inferred as a vague type | Annotate it: `DEFAULT_SETTINGS: dict[str, Any] = {...}` |
| "`__setitem__` not defined on str" after `base \| {...}` | The checker guessed the merged dict's value type | `merged: dict[str, Any] = base \| {...}` |
| `I001` imports not sorted | Missing blank line after imports | `ruff check --fix` |

One root cause (a missing annotation) produced nine errors; fixing it fixed them all. None of these changed how the program ran.

## 5. `UP037` "Remove quotes from type annotation"
Ruff changed `Mapped["Tenant"]` to `Mapped[Tenant]`. That works on Python 3.14 because annotations are evaluated lazily; on 3.13 or older the quotes are needed (a forward reference).

## 6. `E501` line too long
A style rule (line limit 100 here). Fix by wrapping the line; `ruff format` does it for code but not for a long docstring or comment.

## 7. How to treat these messages
1. Read the exact text and the rule code (`E501`, `F401`, `UP037`).
2. Ask what the tool could not prove.
3. Fix the cause (a missing annotation, a name clash), not just the symptom.
4. Use `# noqa: CODE` or `# type: ignore[code]` only when the code is right and the tool cannot see why, and name the specific code.

## Quick check
- Why is `t2` "possibly unbound" and how do I fix it?
- Why was `retry.py` a bad file name?
- What is the correct return type for an `@asynccontextmanager` function?
- Why did a single annotation fix nine `mypy` errors?
