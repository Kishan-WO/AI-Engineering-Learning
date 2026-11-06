# Day 1: Ten things that behave differently from JavaScript

---

## 1. `split()` gives words; looping over a string gives characters

`"a b".split()` returns `["a", "b"]`. `for ch in "a b"` yields `"a"`, `" "`, `"b"`.
`str.split()` with no argument splits on any run of whitespace and drops empty strings.
`str.split(" ")` splits on single spaces and keeps empty strings, like JS's `split(" ")`.

```python
"a  b".split()     # ['a', 'b']
"a  b".split(" ")  # ['a', '', 'b']
```

**Common mistake:** calling `.split()` when you meant to work character by character.
In my palindrome attempt, `filter(str.isalnum, text.split())` threw away whole words like `"man,"`.
**My code:** `excercises.py` #1 and #2, `chunking.py`.

---

## 2. A `def` has no implicit return

A function without `return` gives back `None`. JS arrow functions with an
expression body return implicitly; a Python `def` never does. (`lambda` does, but it
can only hold one expression.)

**Common mistake:** computing the value and forgetting `return`, or using `print`
instead of `return`. The `-> str` hint doesn't stop it at runtime; a type checker like mypy does.
**My code:** `excercises.py` #1, #3, #14, #15 (first versions).

---

## 3. `is None`, not `== None`

`is` checks identity (the same object); `==` checks equality and can be
overridden by a class. `None`, `True` and `False` are single objects, so compare them with `is`.
There is no `===`; `==` is the normal equality check.

**Common mistake:** `if x == None`. Ruff flags it (E711).
Also: `if not x` is not the same as `if x is None`, because `0`, `""` and `[]` are falsy too.
**My code:** `docstore/store.py` (`if doc is None`), `excercises.py` #12 (first version used `== None`).

---

## 4. Default arguments are evaluated once

A default value is created when `def` runs, not on each call. A mutable default
like `[]` or `{}` is one shared object. In JS, `function f(x = [])` creates a new array per call.

```python
def add(tag, tags=[]):  # one list, shared by every call
    tags.append(tag)
    return tags
add("a"); add("b")      # ['a', 'b']
```

**Fix:** default to `None` and create the list inside the body.
Dataclasses use `field(default_factory=list)` and refuse a plain `= []`.
The same "evaluated once" trap hits `created_at: datetime = datetime.now()`.

**Common mistake:** `def f(items=[])` or `def f(config={})`.
**My code:** `bugs.py` (bug 1), `docstore/models.py` (`id`, `tags`, `created_at`).

---

## 5. Copies are shallow

`d.copy()`, `{**d}`, `d | {}`, `list(x)` and `x[:]` copy only the outer container.
Nested lists and dicts are still shared. JS's `{...obj}` and `[...arr]` are shallow too.
Use `copy.deepcopy()` when nested data must be independent.

```python
grid = [[0] * 3] * 3   # three references to ONE inner list
grid[0][0] = 1         # [[1, 0, 0], [1, 0, 0], [1, 0, 0]]
```

**Common mistake:** changing a nested value in a "copy" and changing the original.
**My code:** `bugs.py` (bug 2), `excercises.py` #9 (`merge_settings` is a shallow merge).

---

## 6. `%` with a negative number gives a positive result

Python's `%` takes the sign of the divisor; JS's takes the sign of the dividend.

```python
(-2) % 5   # Python: 3
```
```js
(-2) % 5   // JavaScript: -2
```

Python also has `//` (floor division), and `/` always returns a float: `7 / 2 == 3.5`, `7 // 2 == 3`.

**Common mistake:** porting JS code that adds `+ n` to "fix" negative remainders, which isn't needed.
**My code:** `excercises.py` #10 (`rotate`).

---

## 7. `lambda` holds one expression; comprehensions usually beat `map`/`filter`

`lambda x: x * 2` is like `x => x * 2`, but it can't contain statements or
several lines. For anything bigger, write a `def`. A comprehension usually replaces `map` plus `filter`:

```python
[n ** 2 for n in nums if n % 2 == 0]   # nums.filter(...).map(...)
```

A method can be passed directly instead of wrapped: `filter(str.isalnum, text)`.

**Common mistake:** `lambda x: True if x.isalnum() else False`, which is just `x.isalnum()`.
**My code:** `excercises.py` #2, #11, #13.

---

## 8. Indentation is syntax

Blocks are defined by indentation, not braces. Mixing levels is a syntax
error or, worse, silently changes which block a line belongs to. The standard is 4 spaces (PEP 8).
A `for` / `while` loop can also have an `else` that runs only if the loop didn't `break`.

**Common mistake:** 2-space indentation copied from JS style, mixed with 4-space code.
**Fix:** Ruff extension with format on save.
**My code:** `excercises.py` (still mixed 2 and 4 spaces).

---

## 9. `and` / `or` return an operand, and truthiness is broader

`a or b` returns `a` if it is truthy, otherwise `b`, the same as JS's `||`.
But Python treats more values as falsy: `0`, `""`, `None`, **and empty `[]`, `{}`, `set()`**.
In JS, `[]` and `{}` are truthy.

```python
[] or "default"    # 'default'   (in JS, [] || "default" gives [])
```

Python has no `??`; write `x if x is not None else default`.

**Common mistake:** `name = user_name or "anon"` replaces a legitimate `""` or `0`.
**My code:** `chunking.py` (`if not words`), `docstore/storage.py` (`if not content.strip()`).

---

## 10. Classes: explicit `self`, dunder methods, and `@dataclass`

- Methods take `self` explicitly as their first parameter; there is no implicit `this`.
- `__init__` is the constructor.
- Dunder methods plug a class into built-in syntax: `len(x)` calls `__len__`, `for` calls
  `__iter__`, `in` calls `__contains__`, `==` calls `__eq__`.
- `@dataclass` generates `__init__`, `__repr__` and `__eq__` from type-hinted fields.
- `_name` means "private" by convention only; nothing enforces it (unlike JS's `#name`).
- Interfaces are written with `abc.ABC` and `@abstractmethod`, or `typing.Protocol`.

**Common mistake:** forgetting `self` in a method signature, or writing getters by hand
instead of using a dataclass.
**My code:** `docstore/models.py`, `docstore/store.py`, `docstore/storage.py`.

---

## Bonus: things to remember from today

- `len()` on a joined string counts characters, not words. Single-letter test data hid this bug.
- Slices are end-exclusive: `words[4:7]` includes index 6, so `start + size >= len(words)` means "reached the end".
- Always pass `encoding="utf-8"` when reading or writing files; the Windows default isn't UTF-8.
- `raise X from e` keeps the original error as `e.__cause__`.
