# The `timer` context manager

File: `day-2/timing.py`.

## The code
```python
import time
from typing import Self
from types import TracebackType


class timer:
    def __init__(self, label: str = "block") -> None:
        self.label = label
        self.elapsed = 0.0
        self._start = 0.0

    def __enter__(self) -> Self:
        self._start = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.elapsed = time.perf_counter() - self._start
        print(f"{self.label} took {self.elapsed:.3f}s")
```
Used like this:
```python
with timer("load docs") as t:
    ...
print(t.elapsed)
```

## 1. How `with` uses it
1. Python calls `timer("load docs")`, which creates the object.
2. It calls `__enter__()`. This starts the clock.
3. The value `__enter__` **returns** is what `as t` receives.
4. The block runs.
5. Whatever happens (normal end, `return`, `break` or an exception), Python calls `__exit__(...)`.

## 2. What `__enter__` returns
`__enter__` returns `self`, the `timer` object. That is why `t.elapsed` works after the block. If it returned nothing, `t` would be `None` and `t.elapsed` would raise an `AttributeError`.

## 3. The return type of `__enter__`
```python
def __enter__(self) -> "timer":
```
The hint is quoted because it sits inside `class timer:`, so in older Pythons the name `timer` does not exist yet when Python reads the hint. A quoted name is a **forward reference**.

| Way | Works on |
|---|---|
| `-> "timer"` | any version |
| `-> timer` | 3.14 and later (hints are evaluated lazily); older versions need `from __future__ import annotations` |
| `-> Self` | 3.11+ |

`Self` is the best choice (and what the file uses). It means "the same class as the object this method was called on". If someone writes `class LoggedTimer(timer)`, then `with LoggedTimer() as t:` gives `t` the type `LoggedTimer`. With `-> "timer"` the checker would lose the subclass.

## 4. "timer", `timer` and `timer(...)`: what each one is
| Written as | What it is |
|---|---|
| `class timer:` | The **class** definition. It creates the name `timer` |
| `timer("load")` | An **instance**: one timer object, created by calling the class |
| `-> timer` | A **type hint**: "returns a `timer` instance" |
| `-> "timer"` | The same hint as a **string** (forward reference), read by the checker later |

`timer` the class is a *value* (I can call it); `timer` in a hint is a *type* (I describe data with it). The string form is only for hints.

## 5. Every type in this class
| Type | Meaning |
|---|---|
| `str` | Text. `label: str = "block"` is a string with a default |
| `float` | A number with decimals. `elapsed` and `_start` hold seconds (`0.0`) |
| `None` as a return type | The method returns nothing. `__init__` and `__exit__` return `None` |
| `Self` | The same class as the object the method was called on |
| `BaseException` | The parent of **all** exceptions, including `KeyboardInterrupt` and `CancelledError` |
| `type[BaseException]` | The exception **class** itself (for example `ValueError`), not an instance |
| `type[BaseException] \| None` | An exception class, or `None` when nothing went wrong |
| `BaseException \| None` | An exception **instance** (`ValueError("bad")`), or `None` |
| `TracebackType` | The traceback object: where the error happened (from `types`) |
| `TracebackType \| None` | A traceback, or `None` when the block ended normally |

`type[X]` versus `X`: `ValueError` is a `type[BaseException]`, while `ValueError("bad")` is a `BaseException`. That is why `exc_type` and `exc` have different hints for the same error.

## 6. The `__exit__` parameters and its return value
| Parameter | Meaning |
|---|---|
| `exc_type` | The exception class, or `None` if the block finished normally |
| `exc` | The exception object, or `None` |
| `tb` | The traceback, or `None` |

`__exit__` here has no `return` statement, so it returns `None` automatically: **every Python function that reaches its end without `return` returns `None`.** What `with` does with that value:

| Returned value | Effect |
|---|---|
| `None` (falls off the end), `False` | The exception, if any, **continues upward** |
| `True` (any truthy value) | The exception is **swallowed** |

A timer should record the time and let errors through, so it returns nothing. The test "timer still records and re-raises when the block fails" checks exactly this. (A method that might swallow exceptions would be hinted `-> bool`; this one is `-> None`.)

## 7. Why a class, not `@contextmanager`
| | Class with `__enter__` / `__exit__` | `@contextmanager` generator |
|---|---|---|
| Result available after the block | Yes: `t.elapsed` is an attribute | Needs a mutable object that I fill in a `finally` |
| Amount of code | A bit more | Less |
| Good for | Objects that keep data afterwards | Simple setup and cleanup |

I want `t.elapsed` after the block, so a class is simplest.

## 8. Why `time.perf_counter()`
It is a clock made for measuring short durations, with high resolution. `time.time()` is the wall clock and can jump if the system time changes, which can give wrong or even negative durations.

## Common mistakes
| Mistake | What happens |
|---|---|
| `__enter__` returns nothing | `as t` is `None`; `t.elapsed` fails |
| `__exit__` returns `True` | Every exception inside the block is silently swallowed |
| Using `time.time()` | The clock can jump |
| Reading `t.elapsed` inside the block | It is still `0.0` because `__exit__` has not run |
| Writing `t = timer("x")` without `with` | Nothing starts; `elapsed` stays `0.0` |
| Using `t` in an `except` after `with ... as t` inside `try` | The checker says "possibly unbound"; create the object before the `try` (see `type-checker-messages-and-fixes.md`) |

## Quick check
Answer in my own words:
- What does `with timer("x") as t` put into `t`?
- Why is `-> "timer"` written in quotes, and what is the better alternative?
- What do `exc_type`, `exc` and `tb` contain when the block ends normally?
- What would happen if `__exit__` returned `True`?
- Why does `__exit__` return `None` even though there is no `return`?
- Why is `perf_counter()` better than `time.time()` here?
