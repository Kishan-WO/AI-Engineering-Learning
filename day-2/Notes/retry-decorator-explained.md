# The `@retry` decorator: backoff, jitter and how it plugs into the fetcher

Question: what is `retry_if`, why was `on_retry` and `jitter` removed, and how does `@RETRY` work together with the client, threads and semaphore in the fetcher?

File: `day-2/retry_tools.py`.

## 1. What it does
`@retry(...)` re-runs a function when it fails with one of the listed exceptions, waits between tries, and after the last try raises the last error.

```python
@retry(times=3, base_delay=0.5, max_delay=8.0, exceptions=(ConnectionError, TimeoutError))
def call_api(...): ...
```
| Parameter | Meaning |
|---|---|
| `times` | **Total attempts** (3 = 1 try + 2 retries). Below 1 raises `ValueError` |
| `base_delay` | Wait after the first failure; it doubles after each failure |
| `max_delay` | Upper limit for one wait |
| `exceptions` | Only these exception types are retried; any other is raised at once |

## 2. Three nested functions
A decorator **with arguments** has three levels:
```python
def retry(times, base_delay, max_delay, exceptions):        # level 1: takes the settings
    def decorator(func):                                    # level 2: takes the function
        def wrapper(*args, **kwargs):                       # level 3: runs on every call
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == times - 1:
                        raise                               # last attempt: give up
                    time.sleep(compute_delay(attempt, base_delay, max_delay))
        return wrapper
    return decorator
```
- `@retry(times=3)` first **calls** `retry(...)`, which returns `decorator`; then `decorator(func)` returns `wrapper`.
- After decoration the name points to `wrapper`; the original is held inside it.
- `functools.wraps` keeps the original name and docstring.
- A bare `raise` re-raises the same exception with its traceback.

## 3. Exponential backoff
The wait grows: `base_delay * 2 ** attempt`, capped at `max_delay`.
```python
def backoff_delay(attempt, base_delay, max_delay):
    return min(max_delay, base_delay * 2**attempt)

[backoff_delay(a, 0.5, 8.0) for a in range(6)]
# [0.5, 1.0, 2.0, 4.0, 8.0, 8.0]
```
A struggling server gets more room each time, and the cap keeps the wait reasonable.

## 4. Jitter
```python
def compute_delay(attempt, base_delay, max_delay):
    return random.uniform(0, backoff_delay(attempt, base_delay, max_delay))
```
Jitter means a **random** wait between 0 and the backoff value ("full jitter"). If 100 clients fail together and all retry after exactly 1 s, they hit the server together again. Random waits spread them out. Jitter is always on now (the `jitter` parameter was removed); `backoff_delay` stays separate so the exact numbers can still be tested.

The first wait can be very short (near 0) because it is `uniform(0, delay)`.

## 5. Sync and async from one decorator
```python
if inspect.iscoroutinefunction(func):
    async def async_wrapper(...): ... await asyncio.sleep(delay)
else:
    def wrapper(...): ... time.sleep(delay)
```
- An `async def` function needs `await func(...)` and `await asyncio.sleep(...)`. Using `time.sleep` there would freeze the whole event loop.
- In my test two async calls that each waited 0.05 s finished together in about 0.05 s, not 0.10 s.

## 6. What was removed, and why
| Removed | What it was | Why |
|---|---|---|
| `retry_if` | A function `(exception) -> bool` ("a predicate") that could say "don't retry this one". Useful to retry an HTTP 429 but not a 404 | Kept simpler; the fetcher decides this differently (section 8) |
| `on_retry` | A callback `(attempt, error, delay)` called before each wait | Not needed |
| `jitter` | A flag to turn jitter off | Jitter is always wanted |

## 7. Do not retry everything
`exceptions` is deliberately narrow (`ConnectionError`, `TimeoutError` by default). Retrying a `ValueError` caused by a bug just repeats the bug. Also retry only operations that are **safe to repeat** (a payment could be charged twice).

## 8. How it plugs into the fetcher
```python
RETRY = retry(times=3, base_delay=0.5, exceptions=(httpx.TransportError, RetryableError))

@RETRY
async def fetch_async(client, sem, title): ...
```
- `retry(...)` runs **once** and gives back a decorator stored in `RETRY`; `@RETRY` is `fetch_async = RETRY(fetch_async)`. The same decorator is used on the sync and async functions.
- After that line `fetch_async` is the **wrapper**. When anything calls it, the wrapper loops up to 3 times around the original function.
- What counts as "worth retrying" is decided by `to_record`: it **raises** `RetryableError` for HTTP 429 and 5xx, but only **returns** an error record for 404 and similar. Network failures (`httpx.TransportError`) are retried too.

| Result | What happens |
|---|---|
| 200 | Record returned |
| 429 or 5xx | `RetryableError` raised → wait → try again |
| Timeout, connection reset | `TransportError` → wait → try again |
| 404, 403, ... | Error record returned, **no retry** |

Layers, outside in:
```
gather            starts every title
fetch_async_safe  catches any final failure and returns an error record
wrapper (RETRY)   up to 3 attempts, sleeping between them
fetch_async       takes a semaphore slot, one request, judges the response
```
The semaphore sits **inside** the retried function, so it is released while the wrapper sleeps; a retrying page does not hold one of the 10 slots.

## Common mistakes
| Mistake | What happens |
|---|---|
| `@retry` without parentheses | The decorator receives the function as `times`; use `@retry()` or `@retry(times=3)` |
| `time.sleep` in the async wrapper | The whole loop freezes |
| Retrying every exception | Bugs are repeated and hidden |
| Retrying non-idempotent actions | Duplicate side effects |
| Treating `times` as "number of retries" | It is the **total** number of attempts |

## Quick check
- What are the three nested functions of a decorator with arguments?
- How does the delay grow, and what does jitter add?
- Why does the async version use `await asyncio.sleep`?
- How does `to_record` decide which responses get retried?
- Why is the semaphore inside the retried function?
