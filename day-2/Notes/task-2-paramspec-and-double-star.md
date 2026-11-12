# `**`, `**P` and `ParamSpec`

## 1. The four meanings of `**`
| Where | Meaning | Example |
|---|---|---|
| In a function definition | Collect extra keyword arguments into a dict | `def f(**kwargs)` |
| In a call | Unpack a dict into keyword arguments | `greet(**data)` |
| Inside a dict literal | Merge dicts (shallow copy, later keys win) | `{**a, **b, "z": 3}` |
| Between two numbers | Power | `2 ** 10` is `1024` |

A fifth, type-only use: `**P` inside the brackets of a generic (section 4).

```python
def show(*args, **kwargs):
    print(args, kwargs)

show(1, 2, name="Asha", age=21)
# (1, 2) {'name': 'Asha', 'age': 21}
```
- `*args` collects extra **positional** arguments into a tuple.
- `**kwargs` collects extra **keyword** arguments into a dict.
- A decorator wrapper uses both to pass everything on: `func(*args, **kwargs)`.

## 2. The problem ParamSpec solves
```python
def wrapper(*args, **kwargs):
    return func(*args, **kwargs)
```
It works at runtime for any function, but the type checker has lost the original parameters. After decoration, `slow_add(1, 2)` looks like "accepts anything". The checker can no longer catch `slow_add("x")`.

I want to say: "the wrapper has exactly the same parameters as `func`". Neither `Any` nor an ordinary `TypeVar` can say that.

## 3. `TypeVar` vs `ParamSpec`
| | `TypeVar` (`R`) | `ParamSpec` (`P`) |
|---|---|---|
| Stands for | **One type**, e.g. `int` | A **whole parameter list**, e.g. `(a: int, b: int)` |
| Used as | `-> R`, `list[R]` | `Callable[P, R]`, `*args: P.args`, `**kwargs: P.kwargs` |

```python
def timed(func: Callable[P, R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)
    return wrapper
```
- `Callable[P, R]` means: a function with parameters `P` that returns `R`.
- `P.args` is the positional part and `P.kwargs` is the keyword part of that parameter list.
- The decorated function keeps its exact signature for the checker.

At runtime none of this does anything. The code runs the same without the hints.

## 4. Two ways to declare them
| Old style (3.10+) | New style (3.12+) |
|---|---|
| `P = ParamSpec("P")` | `def timed[**P, R](...)` |
| `R = TypeVar("R")` | (the `R` in `[**P, R]`) |
| Module-level variables, with `from typing import ParamSpec, TypeVar` | In the brackets of the function or class, no imports |

Old style:
```python
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

def timed(func: Callable[P, R]) -> Callable[P, R]: ...
```
New style:
```python
def timed[**P, R](func: Callable[P, R]) -> Callable[P, R]: ...
```
- In the brackets, `R` means a type variable and **`**P` means a ParamSpec**.
- The `**` is what makes it a ParamSpec. A bare `P` would be an ordinary `TypeVar`.

## 5. Don't mix them
```python
P = ParamSpec("P")
R = TypeVar("R")

def timed[P, R](func: Callable[P, R]) -> ...     # wrong
```
- `timed[P, R]` creates **new** `P` and `R` that shadow the module-level ones, so the two lines above it are unused.
- `P` there has no `**`, so it is an ordinary type variable and `P.args` is invalid. mypy would report an error.
- The script still runs, because Python ignores hints at runtime. Only the checker notices.

Fix: choose one style.
- Delete the two module-level lines and write `def timed[**P, R](...)`, or
- keep the module-level lines and write `def timed(func: Callable[P, R]) -> Callable[P, R]:` with no brackets.

I use the new style on Python 3.12+ and the old style when the project must run on older versions.

## Quick check
Answer in my own words:
- What does `**kwargs` collect, and what does `f(**data)` do?
- What can a `ParamSpec` stand for that a `TypeVar` can't?
- What do `P.args` and `P.kwargs` mean?
- What does the `**` in `[**P, R]` do?
- Why is `P = ParamSpec("P")` together with `def timed[P, R]` a mistake?
- Why does the code still run with that mistake?
