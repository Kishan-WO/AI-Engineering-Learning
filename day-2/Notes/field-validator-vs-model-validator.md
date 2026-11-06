# Pydantic: `field_validator` vs `model_validator`, and their parameters

Question: what is the difference between a field validator and a model validator, and what are their parameters?

## 1. The difference in one line
- **`field_validator`** checks or cleans **one field** (or several, one at a time).
- **`model_validator`** checks or cleans the **whole model**, so it can compare fields with each other.

| | `@field_validator("phone")` | `@model_validator(mode="after")` |
|---|---|---|
| Runs for | The named field(s), one value at a time | The whole object |
| Receives | The field's value | The whole model (`after`) or the raw input (`before`) |
| Can see other fields | Only earlier ones, through `info.data` | Yes, all of them (`after`) |
| Typical use | Clean a phone, lowercase a course, parse `"5k"` | `end > start`; "the ai course needs a budget of at least 5000" |
| Error location (`loc`) | The field: `("phone",)` | Empty: `()` |

## 2. `field_validator`
```python
@field_validator("phone", mode="before")
@classmethod
def clean_phone(cls, v: object) -> str:
    return parse_phone(v)
```
**Decorator parameters**
| Parameter | Meaning |
|---|---|
| `*fields` | One or more field names: `@field_validator("name", "city")`. `"*"` means every field |
| `mode` | When it runs: `"after"` (default), `"before"`, `"plain"`, `"wrap"` |
| `check_fields` | `False` allows a name that is not a field (rarely needed) |

**Function parameters**
| Parameter | Meaning |
|---|---|
| `cls` | The class (so `@classmethod` goes underneath) |
| `v` | The value being validated |
| `info` (optional) | A `ValidationInfo`: `info.data` (fields validated **before** this one), `info.field_name`, `info.context`, `info.config` |

**Modes**
| Mode | Runs | `v` is | Use for |
|---|---|---|---|
| `after` (default) | After Pydantic's type check | Already the right type | Extra rules, tidying (`.title()`) |
| `before` | **Before** the type check | Raw input of any type | Cleaning input Pydantic would reject (`"5k"` → `5000`) |
| `wrap` | Around the type check | Raw value plus a `handler` | Fall back when the check fails, or run code before and after |
| `plain` | Replaces the check | Raw value | Fully custom parsing |

Rules:
- It must `return` the value, or the field becomes `None`.
- To reject a value, `raise ValueError("message")`; Pydantic wraps it into a `ValidationError`. Do not raise `ValidationError` yourself.
- Fields validate in declaration order, and a field that **failed** is missing from `info.data`.

In `enquiry.py`: `clean_name` and `clean_city` are `after` (the value is already a `str`); `clean_phone`, `clean_course` and `clean_budget` are `before` (the input could be `"5k"` or an `int`).

## 3. `model_validator`
```python
@model_validator(mode="after")
def ai_needs_budget(self) -> "Enquiry":
    if self.course == "ai" and self.budget < 5000:
        raise ValueError("the ai course needs a budget of at least 5000")
    return self
```
**Decorator parameter:** only `mode`.

| Mode | Runs | Receives | Use for |
|---|---|---|---|
| `after` | After **all** fields passed | The model instance (`self`) | Rules across fields |
| `before` | Before any field is checked | The raw input (usually a dict) | Rename keys, fill defaults, accept other shapes |
| `wrap` | Around everything | Raw input plus `handler` | Rare |

**Shapes**
```python
@model_validator(mode="after")
def check(self) -> "Model": ...                    # instance method; return self

@model_validator(mode="before")
@classmethod
def prepare(cls, data: Any) -> Any: ...            # classmethod; return the (changed) data
```
- `after`: no `@classmethod`, must return `self`.
- `before`: `@classmethod`; `data` may not be a dict, so check `isinstance(data, dict)`.

An `after` model validator **does not run if a field already failed**. In my 30-row test, row 26 (five bad fields) never showed the "ai needs a budget" rule.

## 4. Order of work
```
model before → each field (before → type check → after) → model after
```

## 5. Which one to use
| Need | Use |
|---|---|
| Clean or check one field | `field_validator` (`before` if the raw type would fail) |
| A rule that needs two or more fields | `model_validator(mode="after")` |
| Reshape the input first | `model_validator(mode="before")` |
| A simple range or length rule | Neither: `Field(gt=0, min_length=2)` |

## Common mistakes
| Mistake | What happens |
|---|---|
| Forgetting `@classmethod` under `@field_validator` | Error when the class is defined |
| No `return` | The field becomes `None` |
| `@classmethod` on an `after` model validator | Wrong shape; it is an instance method |
| Cleaning `"5k"` in an `after` validator | The type check rejects it first; use `before` |
| Expecting the model validator to run when fields failed | It does not |

## Quick check
- Why does `clean_budget` use `before` but `clean_name` use `after`?
- Why does `ai_needs_budget` have no `@classmethod`?
- What does `info.data` contain?
- What happens to a model validator when a field is invalid?
