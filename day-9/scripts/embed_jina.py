"""Day 9, task 2: embed every section with one API model (Jina jina-embeddings-v3), in batches.

    .venv\\Scripts\\python scripts\\embed_jina.py --limit 64     # a small trial first
    .venv\\Scripts\\python scripts\\embed_jina.py                # the whole corpus

Reads  corpus/data/sections.json   (made by load_corpus.py)  and  day-9/.env  (JINA_API_KEY).
Writes corpus/data/embeddings/jina-embeddings-v3/
          vectors.npy   float32, shape (number of sections, 1024); row i is section i of meta.json
          meta.json     the model settings, one entry per row (id, source, title, heading path, a hash
                        of the text that was embedded) and the run statistics (tokens, time, retries)
          batches/      one small file per batch, written as soon as the batch returns, so a run that
                        stops (a network error, a limit) continues where it stopped when started again

What is embedded for a section: its heading path, a blank line, then its text. The same text will be
given to the open model in task 5, so the two models are compared on the same input.

Limits it respects (free key, from the Jina rate-limit table): 100 requests and 100,000 tokens per
minute. It stays under 90 requests and 90,000 tokens per minute, counting its own estimate before a
call and Jina's real count after it. The key is never printed.
"""

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "corpus" / "data"

MODEL = "jina-embeddings-v3"
TASK = "retrieval.passage"  # the document side; the queries will use retrieval.query
DIMENSIONS = 1024
URL = "https://api.jina.ai/v1/embeddings"

BATCH_TEXTS = 32  # most texts in one request
BATCH_TOKENS = 12_000  # most estimated tokens in one request
TOKENS_PER_MINUTE = 90_000  # under Jina's 100,000
REQUESTS_PER_MINUTE = 90  # under Jina's 100
MAX_ATTEMPTS = 6


def read_key() -> str:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("JINA_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("JINA_API_KEY is not in day-9/.env")


def embed_text(section: dict) -> str:
    """The text that is embedded: the heading path, then the section text."""
    return " > ".join(section["heading_path"]) + "\n\n" + section["text"]


def estimate_tokens(text: str) -> int:
    """A rough count before the call (the real count comes back with the answer)."""
    return int(max(len(text.split()) * 1.35, len(text) / 4)) + 8


def make_batches(texts: list[str]) -> list[list[int]]:
    batches: list[list[int]] = []
    current: list[int] = []
    tokens = 0
    for i, text in enumerate(texts):
        t = estimate_tokens(text)
        if current and (len(current) >= BATCH_TEXTS or tokens + t > BATCH_TOKENS):
            batches.append(current)
            current, tokens = [], 0
        current.append(i)
        tokens += t
    if current:
        batches.append(current)
    return batches


class Pacer:
    """Keeps the requests and tokens of the last 60 seconds under the budget."""

    def __init__(self) -> None:
        self.events: deque[list] = deque()  # [time, tokens]

    def wait_for(self, tokens: int) -> float:
        waited = 0.0
        while True:
            now = time.monotonic()
            while self.events and now - self.events[0][0] >= 60:
                self.events.popleft()
            used = sum(e[1] for e in self.events)
            if used + tokens <= TOKENS_PER_MINUTE and len(self.events) < REQUESTS_PER_MINUTE:
                return waited
            pause = max(60 - (now - self.events[0][0]), 0.5) if self.events else 1.0
            time.sleep(pause)
            waited += pause

    def record(self, tokens: int) -> list:
        event = [time.monotonic(), tokens]
        self.events.append(event)
        return event


def request_batch(key: str, inputs: list[str]) -> tuple[list[list[float]], int, int]:
    """One embeddings request. Returns the vectors, Jina's token count, and how many retries it needed."""
    body = {"model": MODEL, "task": TASK, "dimensions": DIMENSIONS, "late_chunking": False, "truncate": False, "input": inputs}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "Accept": "application/json"}
    retries = 0
    for attempt in range(1, MAX_ATTEMPTS + 1):
        req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.load(r)
            items = sorted(data["data"], key=lambda d: d["index"])
            if len(items) != len(inputs):
                raise RuntimeError(f"asked for {len(inputs)} vectors, got {len(items)}")
            return [d["embedding"] for d in items], int(data["usage"]["total_tokens"]), retries
        except urllib.error.HTTPError as e:
            detail = e.read()[:300].decode("utf-8", "replace")
            if e.code == 429 or e.code >= 500:
                retries += 1
                pause = min(10 * 2 ** (attempt - 1), 90)
                print(f"   HTTP {e.code}, waiting {pause}s (attempt {attempt}/{MAX_ATTEMPTS})", flush=True)
                time.sleep(pause)
                continue
            sys.exit(f"HTTP {e.code}: {detail}")  # a 4xx other than 429 is a mistake of mine: stop, do not retry
        except (urllib.error.URLError, TimeoutError) as e:
            retries += 1
            pause = min(5 * 2 ** (attempt - 1), 60)
            print(f"   network problem ({type(e).__name__}), waiting {pause}s (attempt {attempt}/{MAX_ATTEMPTS})", flush=True)
            time.sleep(pause)
    sys.exit("giving up after repeated failures; run the script again to continue from the saved batches")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="embed only the first N sections (a trial run)")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

    sections = json.loads((DATA / "sections.json").read_text(encoding="utf-8"))
    if args.limit:
        sections = sections[: args.limit]
    texts = [embed_text(s) for s in sections]
    hashes = [hashlib.sha256(t.encode("utf-8")).hexdigest() for t in texts]
    batches = make_batches(texts)

    name = MODEL + (f"__first{args.limit}" if args.limit else "")
    out = DATA / "embeddings" / name
    (out / "batches").mkdir(parents=True, exist_ok=True)
    key = read_key()
    print(f"{len(sections)} sections in {len(batches)} batches -> {out.relative_to(ROOT)}")
    print(f"estimated tokens: {sum(estimate_tokens(t) for t in texts):,}\n")

    pacer = Pacer()
    started = time.time()
    stats = {"tokens": 0, "retries": 0, "waited_seconds": 0.0, "api_seconds": 0.0, "batches_done": 0, "batches_reused": 0}
    batch_log: list[dict] = []
    parts: list[np.ndarray] = []
    for n, idx in enumerate(batches):
        ids = [sections[i]["id"] for i in idx]
        npy, js = out / "batches" / f"batch_{n:04d}.npy", out / "batches" / f"batch_{n:04d}.json"
        if npy.exists() and js.exists():
            saved = json.loads(js.read_text(encoding="utf-8"))
            if saved["ids"] == ids and saved["hashes"] == [hashes[i] for i in idx]:
                parts.append(np.load(npy))
                stats["batches_reused"] += 1
                stats["tokens"] += saved["tokens"]
                batch_log.append(saved["log"])
                print(f"batch {n + 1}/{len(batches)}: reused from disk")
                continue
        est = sum(estimate_tokens(texts[i]) for i in idx)
        waited = pacer.wait_for(est)
        event = pacer.record(est)
        t0 = time.perf_counter()
        vectors, tokens, retries = request_batch(key, [texts[i] for i in idx])
        elapsed = time.perf_counter() - t0
        event[1] = tokens  # replace the estimate by the real count
        arr = np.array(vectors, dtype=np.float32)
        np.save(npy, arr)
        log = {"batch": n, "texts": len(idx), "tokens": tokens, "estimated_tokens": est, "seconds": round(elapsed, 3), "retries": retries}
        js.write_text(json.dumps({"ids": ids, "hashes": [hashes[i] for i in idx], "tokens": tokens, "log": log}), encoding="utf-8")
        parts.append(arr)
        batch_log.append(log)
        stats["tokens"] += tokens
        stats["retries"] += retries
        stats["waited_seconds"] += waited
        stats["api_seconds"] += elapsed
        stats["batches_done"] += 1
        print(f"batch {n + 1}/{len(batches)}: {len(idx)} texts, {tokens:,} tokens (estimated {est:,}), {elapsed:.1f}s, waited {waited:.0f}s | total {stats['tokens']:,} tokens", flush=True)

    vectors = np.concatenate(parts).astype(np.float32)
    norms = np.linalg.norm(vectors, axis=1)
    if vectors.shape != (len(sections), DIMENSIONS):
        sys.exit(f"unexpected shape {vectors.shape}")
    if not np.all(np.isfinite(vectors)):
        sys.exit("the vectors contain NaN or infinity")
    normalised = bool(np.allclose(norms, 1.0, atol=1e-3))
    np.save(out / "vectors.npy", vectors)

    meta = {
        "model": MODEL,
        "provider": "Jina AI (API)",
        "task": TASK,
        "dimensions": DIMENSIONS,
        "late_chunking": False,
        "truncate": False,
        "dtype": "float32",
        "normalised_by_provider": normalised,
        "norm_min": round(float(norms.min()), 6),
        "norm_max": round(float(norms.max()), 6),
        "embedded_text": "heading path joined by ' > ', a blank line, then the section text",
        "query_task": "retrieval.query",
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run": {
            "sections": len(sections),
            "batches": len(batches),
            "total_tokens_billed": stats["tokens"],
            "price": "free tier (10M tokens per new key); not billed in USD",
            # from the per-batch log, so they stay right when a run was stopped and continued
            "seconds_in_api_calls": round(sum(b["seconds"] for b in batch_log), 1),
            "retries": sum(b["retries"] for b in batch_log),
            "seconds_this_run": round(time.time() - started, 1),
            "seconds_waiting_for_the_limit_this_run": round(stats["waited_seconds"], 1),
            "batches_reused_from_disk_this_run": stats["batches_reused"],
            "batch_log": batch_log,
        },
        "rows": [
            {"row": i, "id": s["id"], "doc_id": s["doc_id"], "source": s["source"], "title": s["title"],
             "heading_path": s["heading_path"], "words": s["words"], "licence": s["licence"], "text_sha256": hashes[i]}
            for i, s in enumerate(sections)
        ],
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nsaved {vectors.shape} float32 ({vectors.nbytes / 1e6:.1f} MB) and meta.json")
    print(f"norms: min {norms.min():.4f}, max {norms.max():.4f} (normalised: {normalised})")
    print(f"tokens billed: {stats['tokens']:,} | time: {time.time() - started:.0f}s (waiting for the limit: {stats['waited_seconds']:.0f}s) | retries: {stats['retries']}")


if __name__ == "__main__":
    main()
