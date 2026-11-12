# The mutable default argument, with the `None` pattern

Question: "Why is `tags` `None` the second time, when it should be a list? And if it is `None`, why does it still append to a shared list?"

I was mixing up two different functions: the **buggy** one (default `[]`) and the **fixed** one (default `None`). Here they are side by side.

## 1. The two functions
```python
def add_tag_buggy(tag, tags=[]):          # default is a list
    tags.append(tag)
    return tags

def add_tag_fixed(tag, tags=None):        # default is None
    if tags is None:
        tags = []                         # a NEW list, made inside the call
    tags.append(tag)
    return tags
```

## 2. What happens, measured
```python
a = add_tag_buggy("python");  b = add_tag_buggy("fastapi")
# a and b:                ['python', 'fastapi']  ['python', 'fastapi']
# a is b:                 True            <- the very same list object
# add_tag_buggy.__defaults__[0]:  ['python', 'fastapi']   <- the default itself changed

c = add_tag_fixed("python");  d = add_tag_fixed("fastapi")
# c and d:                ['python']  ['fastapi']
# c is d:                 False
# add_tag_fixed.__defaults__:     (None,)         <- the default is still None
```

## 3. Why the buggy one shares the list
A default value is created **once, when the `def` statement runs**, not on every call. The list `[]` is created one time, stored on the function (`__defaults__`), and every call that does not pass `tags` uses **that same list**. Each `append` changes it, so the next call sees the earlier items.

JavaScript creates the default again on every call (`function f(x = [])`), so this surprises JS developers.

## 4. Why the fixed one does not
- The default is `None`: **immutable**, so it can be shared safely. Nothing can change it.
- The line `tags = []` runs **inside the call**, so every call that gets `None` builds its own fresh list.
- `tags` is `None` only at the start of the call. After `if tags is None: tags = []`, the name points to a real list, and the append goes to that private list, not to a shared one.

This answers my question: the `None` is a **signal meaning "make a new list"**, not the list that gets appended to.

## 5. The same mistake with dataclasses
```python
tags: list[str] = []                       # dataclass refuses this (ValueError)
tags: list[str] = field(default_factory=list)   # a new list for every object
```
`default_factory` is the dataclass version of the `None` pattern. Pydantic models copy such defaults for each instance automatically.

## 6. Which defaults are safe
| Safe (immutable) | Dangerous (mutable) |
|---|---|
| `None`, numbers, strings, `True`, tuples | `[]`, `{}`, `set()`, an object instance |

## 7. Related: shallow vs deep copy
`dict.copy()`, `{**d}` and `list(x)` copy only the **outer** container; nested lists and dicts are still the same objects:

```python
user = defaults.copy()
user["llm"]["temperature"] = 0.9      # also changes defaults["llm"]
```
Use `copy.deepcopy(defaults)` when nested data must be independent. The same trap: `[[0] * 3] * 3` repeats **one** inner list three times; `[[0] * 3 for _ in range(3)]` makes three.

## Common mistakes
| Mistake | What happens |
|---|---|
| `def f(x=[])` | The list is shared by all calls |
| Using `if not tags:` instead of `if tags is None:` | A list the caller passed in empty gets replaced by a new one |
| `dict.copy()` for nested settings | Edits leak into the original |
| Reading `__defaults__` and thinking it is per call | It is one stored tuple for the function |

## Quick check
- When is a default value created?
- Why is `None` safe as a default, and what does it signal?
- Why does the second call of the buggy function see the first call's tag?
- What is the dataclass equivalent of the `None` pattern?
