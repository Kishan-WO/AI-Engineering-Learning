"""Day 2, task 5: fetch 100+ Wikipedia summaries sequentially, with threads, and with asyncio."""

import asyncio
import json
import os
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from dotenv import load_dotenv

from retry_tools import retry

BASE_URL = "https://en.wikipedia.org"
load_dotenv()
CONTACT = os.environ.get("WIKI_CONTACT", "")
HEADERS = {"User-Agent": f"ai-eng-learning/0.1 ({CONTACT})"}
TIMEOUT = httpx.Timeout(10.0, connect=5.0)
CONCURRENCY = 10
TITLES_FILE = Path(__file__).with_name("titles.json")  # cached so every run (and every version) uses the same pages

Record = dict[str, Any]


class RetryableError(Exception):
    """The server said 'try again later' (429) or failed (5xx). 404 and friends are not retryable."""


def get_titles(count: int = 120) -> list[str]:
    """A fixed list of random article titles, fetched once and cached in titles.json."""
    if TITLES_FILE.exists():
        cached = json.loads(TITLES_FILE.read_text(encoding="utf-8"))
        if len(cached) >= count:
            return cached[:count]
    response = httpx.get(
        f"{BASE_URL}/w/api.php",
        params={"action": "query", "list": "random", "rnnamespace": 0, "rnlimit": count + 20, "format": "json"},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    titles = list(dict.fromkeys(item["title"] for item in response.json()["query"]["random"]))[:count]
    TITLES_FILE.write_text(json.dumps(titles, ensure_ascii=False, indent=2), encoding="utf-8")
    return titles


def summary_path(title: str) -> str:
    return f"/api/rest_v1/page/summary/{quote(title.replace(' ', '_'), safe='')}"


def to_record(title: str, response: httpx.Response) -> Record:
    """200 -> a record; 429/5xx -> raise RetryableError (so @retry tries again); other codes -> an error record."""
    if response.status_code == 200:
        return {"title": title, "chars": len(response.json().get("extract", ""))}
    if response.status_code == 429 or response.status_code >= 500:
        raise RetryableError(f"HTTP {response.status_code}")
    return {"title": title, "error": f"HTTP {response.status_code}"}


def failure(title: str, error: Exception) -> Record:
    return {"title": title, "error": f"{type(error).__name__}: {error}"}


RETRY = retry(times=3, base_delay=0.5, exceptions=(httpx.TransportError, RetryableError))


### =============== 1. sequential ===============

@RETRY
def fetch_sync(client: httpx.Client, title: str) -> Record:
    return to_record(title, client.get(summary_path(title)))


def fetch_sync_safe(client: httpx.Client, title: str) -> Record:
    try:
        return fetch_sync(client, title)
    except Exception as error:  # one bad page must not stop the others
        return failure(title, error)


def run_sequential(titles: list[str]) -> list[Record]:
    with httpx.Client(base_url=BASE_URL, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
        return [fetch_sync_safe(client, title) for title in titles]


### =============== 2. threads ===============

def run_threaded(titles: list[str]) -> list[Record]:
    with httpx.Client(base_url=BASE_URL, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
        with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
            return list(pool.map(lambda title: fetch_sync_safe(client, title), titles))


### =============== 3. asyncio ===============

in_flight = {"now": 0, "peak": 0}  # used by the checks to prove the semaphore works


@RETRY
async def fetch_async(client: httpx.AsyncClient, sem: asyncio.Semaphore, title: str) -> Record:
    async with sem:  # only the request is limited; the semaphore is free again while retry waits
        in_flight["now"] += 1
        in_flight["peak"] = max(in_flight["peak"], in_flight["now"])
        try:
            response = await client.get(summary_path(title))
        finally:
            in_flight["now"] -= 1
    return to_record(title, response)


async def fetch_async_safe(client: httpx.AsyncClient, sem: asyncio.Semaphore, title: str) -> Record:
    try:
        return await fetch_async(client, sem, title)
    except Exception as error:
        return failure(title, error)


async def run_async(titles: list[str]) -> list[Record]:
    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient(base_url=BASE_URL, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
        return list(await asyncio.gather(*(fetch_async_safe(client, sem, title) for title in titles)))


### =============== report ===============

def timed_run(label: str, run: Callable[[], list[Record]]) -> tuple[list[Record], float]:
    start = time.perf_counter()
    records = run()
    elapsed = time.perf_counter() - start
    ok = sum("chars" in r for r in records)
    print(f"{label:<22} {elapsed:6.2f}s   ok {ok}, failed {len(records) - ok}")
    return records, elapsed


if __name__ == "__main__":
    if not CONTACT:
        raise SystemExit("Fill in WIKI_CONTACT in the .env file (an email or URL; Wikimedia requires it in the User-Agent).")
    titles = get_titles(120) + ["Definitely_Not_A_Real_Page_xyz123"]  # one page that must fail with a 404
    print(f"{len(titles)} pages, concurrency {CONCURRENCY}\n")

    sequential, t_seq = timed_run("sequential", lambda: run_sequential(titles))
    threaded, t_thr = timed_run(f"threads ({CONCURRENCY})", lambda: run_threaded(titles))
    asynced, t_async = timed_run(f"asyncio (sem {CONCURRENCY})", lambda: asyncio.run(run_async(titles)))

    print("\nfailures (async run):")
    for record in asynced:
        if "error" in record:
            print(f"  {record['title']}: {record['error']}")

    print(f"\nthreads are {t_seq / t_thr:.1f}x and asyncio is {t_seq / t_async:.1f}x faster than sequential")

    print("\n--- checks ---")
    assert [r["title"] for r in sequential] == [r["title"] for r in threaded] == [r["title"] for r in asynced] == titles
    print("1. all three versions return the same titles in the same order: PASS")

    assert in_flight["peak"] <= CONCURRENCY, in_flight
    print(f"2. at most {CONCURRENCY} async requests in flight (peak {in_flight['peak']}): PASS")

    bad = [r for r in asynced if "error" in r]
    assert any(r["title"].startswith("Definitely_Not") and r["error"] == "HTTP 404" for r in bad)
    assert len(asynced) - len(bad) >= len(titles) - len(bad) > 0
    print(f"3. the 404 page failed alone; {len(asynced) - len(bad)} other pages still succeeded: PASS")

    assert t_async < t_seq / 3, (t_async, t_seq)
    print("4. asyncio is more than 3x faster than sequential: PASS")

    print("\nall fetcher checks passed")
