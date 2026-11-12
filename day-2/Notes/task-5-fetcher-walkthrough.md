# `task5_fetcher.py`, part by part

Question: explain `task5_fetcher.py` one line at a time. The task: fetch 100+ Wikipedia summaries three ways (one by one, with threads, with asyncio) and compare.

How `@RETRY` fits in is in `task-1-retry-decorator-explained.md`; the `*` in `gather` is in `day-1/learning/star-and-double-star-unpacking.md`.

## 1. Imports
`asyncio` (event loop, semaphore, gather), `json` (titles cache), `os` (environment variable), `time` (timing), `Callable` (type hint), `ThreadPoolExecutor` (threads), `Path` (file paths), `Any` (type hint), `quote` (URL-encode a title), `httpx` (HTTP client), `load_dotenv` (reads `.env`), and my own `retry` from `task1_retry.py`.

## 2. Settings
```python
BASE_URL = "https://en.wikipedia.org"
load_dotenv()
CONTACT = os.environ.get("WIKI_CONTACT", "")
HEADERS = {"User-Agent": f"ai-eng-learning/0.1 ({CONTACT})"}
TIMEOUT = httpx.Timeout(10.0, connect=5.0)
CONCURRENCY = 10
TITLES_FILE = Path(__file__).with_name("titles.json")
Record = dict[str, Any]
```
- `load_dotenv()` reads `.env` into environment variables. Wikimedia blocks anonymous clients (403), so a contact goes in the `User-Agent`; it lives in `.env`, not in the code (see `task-5-dotenv-and-environment-variables.md`).
- `TIMEOUT`: 10 s for each phase, 5 s to connect.
- `CONCURRENCY = 10` is used for both the thread pool and the semaphore.
- `TITLES_FILE`: `titles.json` next to this file (`__file__` is this file's path).
- `Record`: a name for `dict[str, Any]`. A record is `{"title", "chars"}` on success or `{"title", "error"}` on failure.

## 3. `RetryableError`
An empty exception class. It is the signal from `to_record` to `@RETRY`: "this failure is worth another try".

## 4. `get_titles(count)`
Returns a fixed list of random article titles.
1. If `titles.json` exists and has enough titles, return them. Every run and every version then uses the **same** pages.
2. Otherwise call the Wikipedia search API (`list=random`, article namespace only, `count + 20` to allow for duplicates).
3. `raise_for_status()` turns 4xx/5xx into an exception.
4. `dict.fromkeys(...)` removes duplicates **and keeps order**; `[:count]` trims the list.
5. Save to `titles.json` (`ensure_ascii=False` keeps non-English letters readable) and return.

## 5. `summary_path(title)`
Builds `/api/rest_v1/page/summary/<title>`: spaces become underscores, and `quote(..., safe='')` encodes every special character, including `/`. Only the path is returned, because the client already knows `BASE_URL`.

## 6. `to_record(title, response)`
| Response | Result |
|---|---|
| 200 | Return `{"title", "chars"}` (`chars` = length of the `extract` text) |
| 429 or 5xx | **Raise** `RetryableError`, so `@RETRY` tries again |
| anything else (404, 403 ...) | **Return** an error record; no exception, no retry |

## 7. `failure(title, error)`
Turns an exception into an error record: `{"error": "ReadTimeout: ..."}`.

## 8. `RETRY`
`retry(times=3, base_delay=0.5, exceptions=(httpx.TransportError, RetryableError))` is built **once** and used as a decorator on both the sync and the async function.

## 9. Version 1: sequential
```python
@RETRY
def fetch_sync(client, title):
    return to_record(title, client.get(summary_path(title)))

def fetch_sync_safe(client, title):
    try:    return fetch_sync(client, title)
    except Exception as error:  return failure(title, error)

def run_sequential(titles):
    with httpx.Client(base_url=BASE_URL, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
        return [fetch_sync_safe(client, title) for title in titles]
```
- One `httpx.Client` for the whole run (connection pool, shared settings); `with` closes it.
- `fetch_sync_safe` is the safety net: after all retries, any failure becomes an error record, so **one bad page cannot stop the other 120**.
- The list comprehension requests one title after another.

## 10. Version 2: threads
```python
with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
    return list(pool.map(lambda title: fetch_sync_safe(client, title), titles))
```
- At most 10 requests at a time, in a pool of threads, sharing the one client.
- `pool.map` returns results **in input order**. The `lambda` supplies `client` because `map` passes only the title.

## 11. Version 3: asyncio
```python
in_flight = {"now": 0, "peak": 0}

@RETRY
async def fetch_async(client, sem, title):
    async with sem:
        in_flight["now"] += 1
        in_flight["peak"] = max(in_flight["peak"], in_flight["now"])
        try:
            response = await client.get(summary_path(title))
        finally:
            in_flight["now"] -= 1
    return to_record(title, response)
```
- `async with sem:` waits for one of the 10 slots. Only the request is inside; the slot is **free again while `@RETRY` is sleeping** before a retry.
- `in_flight` counts requests currently running and the highest count seen; a check uses it to prove the limit of 10 held.
- `await client.get(...)` lets the event loop run other pages while this one waits.
- The status is judged **after** leaving the `async with`.

```python
async def run_async(titles):
    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient(...) as client:
        return list(await asyncio.gather(*(fetch_async_safe(client, sem, title) for title in titles)))
```
- The semaphore is created **inside** the running loop; one shared `AsyncClient`.
- `gather(*(...))` starts all 121 tasks at once, but the semaphore lets only 10 do a request at a time. Results come back in input order.

## 12. `timed_run(label, run)`
`run` is a function with no arguments (callers pass a `lambda`). It times the call with `perf_counter()`, counts records that have a `"chars"` key as OK, prints one line, and returns both the records and the time.

## 13. The main block
1. Stop with a clear message if `WIKI_CONTACT` is empty.
2. Get 120 titles and append one **fake** page that must come back as a 404.
3. Run the three versions with `timed_run` and print the speed-ups.
4. Checks:
   - all three versions return the same titles in the same order,
   - at most 10 async requests were ever in flight,
   - the fake page failed on its own with `HTTP 404` while the others succeeded,
   - asyncio is more than 3 times faster than sequential.

## The flow
```
get_titles → 121 titles
  sequential  one request at a time
  threads     10 at a time (pool)
  asyncio     10 at a time (semaphore)

each request: client.get → to_record
   200 → record     404 → error record     429/5xx → raise → @RETRY → wait → again
any final failure → error record (the run never stops)
```

## Quick check
- Why is `titles.json` cached?
- What decides whether a response is retried?
- Why does `fetch_async_safe` exist?
- What does `pool.map` guarantee about order?
- Why is the semaphore released while a retry sleeps?
