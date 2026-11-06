# `*` and `**`: collecting and unpacking

Question: what does the `*` mean in `await asyncio.gather(*(fetch_async_safe(client, sem, title) for title in titles))`, and earlier, what is `**`?

The same symbols do two opposite jobs depending on **where** they appear.

## 1. In a function definition: collect
```python
def show(*args, **kwargs):
    return args, kwargs

show(1, 2, k=3)      # ((1, 2), {'k': 3})
```
| Symbol | Collects | Into |
|---|---|---|
| `*args` | extra positional arguments | a tuple |
| `**kwargs` | extra keyword arguments | a dict |

(A bare `*` in a definition starts the keyword-only zone: see `keyword-only-arguments.md`.)

## 2. In a call: unpack
```python
def add3(a, b, c): return a + b + c

nums = [1, 2, 3]
add3(*nums)                       # 6, same as add3(1, 2, 3)
show(*[1, 2], **{"k": 3})         # ((1, 2), {'k': 3})
print(*(n * n for n in range(4)))   # 0 1 4 9
```
- `*iterable` spreads **any iterable** (list, tuple, set, generator) into separate positional arguments.
- `**mapping` spreads a dict into keyword arguments.

## 3. In assignments and literals
```python
first, *rest = [10, 20, 30, 40]     # first=10, rest=[20, 30, 40]

a = {"x": 1}
b = {"y": 2, "x": 9}
{**a, **b}                          # {'x': 9, 'y': 2}   later keys win
[*list1, *list2]                    # merge lists
```
JavaScript equivalents: `const [first, ...rest] = arr`, `{...a, ...b}`, `[...a, ...b]`. JS uses the same `...` for both collecting and spreading; Python uses `*`/`**`.

## 4. The `gather` line
```python
await asyncio.gather(*(fetch_async_safe(client, sem, title) for title in titles))
```
- `asyncio.gather` takes the awaitables as **separate arguments**: `gather(coro1, coro2, coro3)`.
- The part in parentheses is a **generator expression** that produces one coroutine per title.
- The `*` turns that generator into separate arguments, as if I had written them one by one.

Real results:
```
gather(*coros)  -> [0, 2, 4]
gather([list])  -> TypeError   (a list is one argument, and not awaitable)
```
The same in JavaScript needs no spread: `Promise.all(titles.map(...))` takes one array.

Equivalent form that keeps a list:
```python
coros = [fetch_async_safe(client, sem, title) for title in titles]
results = await asyncio.gather(*coros)
```

## 5. `**` as power
`2 ** 10` is `1024`, the same as in JavaScript. The meaning depends on where it sits: between two numbers it is power; in a definition, call or dict literal it is the dict version of `*`.

## Summary table
| Where | `*` | `**` |
|---|---|---|
| `def f(...)` | collect extra positional → tuple | collect extra keyword → dict |
| `f(...)` call | spread an iterable into arguments | spread a dict into keyword arguments |
| Assignment | `first, *rest = items` | not allowed |
| Literal | `[*a, *b]` | `{**a, **b}` |
| Between numbers | multiply | power |

## Common mistakes
| Mistake | What happens |
|---|---|
| `gather([coro1, coro2])` | `TypeError`; the list is one argument |
| `f(*mapping)` with a dict | Spreads the **keys**, not the values |
| Unpacking a very large generator | It is fully consumed into the argument list |
| `f(**d)` with a key that is not a parameter | `TypeError: unexpected keyword argument` |

## Quick check
- What does `*` do in a definition, and what does it do in a call?
- Why does `asyncio.gather` need the `*` in front of the generator?
- What does `{**a, **b}` do when both have the same key?
- What does `first, *rest = items` assign?
