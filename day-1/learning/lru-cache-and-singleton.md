# `functools.lru_cache` and the cached settings object

Where I met it:
```python
@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
```

## 1. What `lru_cache` does
`lru_cache` is a decorator from `functools`. It **remembers the result of a function call**, keyed by the arguments. Calling the function again with the same arguments returns the saved result instead of running the body.

```python
import functools

@functools.lru_cache
def get_settings():
    print("building...")
    return object()

a = get_settings()    # body runs
b = get_settings()    # body does NOT run, same object returned
print(a is b)         # True
```
Real output from my test:
```
same object: True | body ran 1 time(s) | CacheInfo(hits=1, misses=1, maxsize=128, currsize=1)
after cache_clear, new object: True | body ran 2 times
```
- `hits=1, misses=1`: the first call was a miss (computed), the second a hit (reused).
- `maxsize=128`: it keeps the 128 most recently used results ("LRU" = least recently used is thrown away first). `@lru_cache(maxsize=None)` or `@functools.cache` keeps everything.
- `get_settings.cache_clear()` empties the cache, so the next call computes again. Useful in tests.

## 2. Why the settings use it
Building `Settings()` reads the `.env` file and validates every value. I want that **once**, not on every request. With `@lru_cache`:
- The first call builds the object. Every later call returns the same one.
- That makes it behave like a **singleton**: one shared settings object for the whole program.

JavaScript comparison:
```javascript
let settings;
export function getSettings() { return (settings ??= loadSettings()); }
```
`lru_cache` does the same without the global variable.

## 3. Rules to remember
| Rule | Reason |
|---|---|
| Arguments must be **hashable** (numbers, strings, tuples) | They are used as the dictionary key. A list argument raises `TypeError: unhashable` |
| Use it for **pure** functions (same input, same output) | A cached result never changes, even if the world does |
| The cache lives as long as the process | Changing `.env` while running has no effect until restart or `cache_clear()` |
| Don't use it on methods holding large objects | The cache keeps `self` alive |

## 4. In tests
Because the settings are cached, a test that wants different settings has two options:
- set the environment variables **before** anything imports the app, or
- call `get_settings.cache_clear()` after changing them.

## Common mistakes
| Mistake | What happens |
|---|---|
| Expecting the cache to notice a changed `.env` | It returns the old object until cleared |
| Passing a list or dict argument | `TypeError: unhashable type` |
| Caching a function with side effects | The side effect happens only once |
| Forgetting `maxsize` means 128 entries by default | Old results may be dropped silently |

## Quick check
- What does `@lru_cache` do on the second call with the same arguments?
- Why is it a good fit for `get_settings()`?
- What do `hits` and `misses` in `cache_info()` mean?
- How do I make the next call recompute?
