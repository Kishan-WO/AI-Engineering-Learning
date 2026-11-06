# Keyword-only arguments: the `*` in a function definition

Where I met it: `async def register(session: AsyncSession, *, email: str, password: str, tenant_name: str)`.

## 1. What a lone `*` means
A bare `*` in the parameter list is a **divider**:
- Parameters **before** it can be passed by position or by name.
- Parameters **after** it can only be passed **by name**.

```python
def register(session, *, email, password):
    return f"{session}:{email}"

register("s", email="a@x.com", password="p")     # fine
register("s", "a@x.com", "p")                    # TypeError
```
Real error:
```
TypeError: register() takes 1 positional argument but 3 were given
```

## 2. Why it is useful
- **Calls read clearly.** `register(session, email=..., password=...)` is self-explanatory, while `register(session, "a@x.com", "secret", "Acme")` is a guessing game.
- **Order mistakes are impossible.** With two string parameters (`email`, `password`) it is easy to swap them silently. Names make that a visible error.
- **Safe to change later.** I can add, remove or reorder keyword-only parameters without breaking callers that use names.

JavaScript has no such thing. The closest habit is passing one object: `register(session, { email, password })`.

## 3. The mirror: positional-only `/`
A `/` in the list makes everything **before** it positional-only:

```python
def pos_only(a, b, /, c):
    return a + b + c

pos_only(1, 2, c=3)        # fine
pos_only(a=1, b=2, c=3)    # TypeError: got some positional-only arguments passed as keyword arguments: 'a, b'
```
Used when the parameter names are not part of the public API (many built-in functions work like this).

## 4. All the parameter kinds in one signature
```python
def f(pos_only, /, normal, *, kw_only):
    ...
```
| Zone | How it can be passed |
|---|---|
| before `/` | position only |
| between `/` and `*` | position or name |
| after `*` | name only |

## 5. Not the same as `*args`
| Syntax | Meaning |
|---|---|
| `def f(*args)` | collect **extra positional** arguments into a tuple. Everything after `*args` is also keyword-only |
| `def f(*, x)` | a bare `*` collects nothing; it only starts the keyword-only zone |
| `f(*items)` in a **call** | unpack a list into separate arguments |

## Common mistakes
| Mistake | What happens |
|---|---|
| Passing a keyword-only parameter by position | `TypeError ... positional argument(s) but N were given` |
| Putting the `*` first when I want some positional parameters | They become keyword-only too |
| Confusing the bare `*` with unpacking in a call | One is in a `def`, the other in a call |

## Quick check
- What does the `*` in `register(session, *, email, password)` do?
- Why is `register(s, "a@x.com", "p")` an error?
- What does `/` do?
- Give two reasons to make parameters keyword-only.
