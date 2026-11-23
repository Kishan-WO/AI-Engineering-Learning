"""Day 9, task 5: benchmark Jina vs BGE-M3 on recall@5, latency and cost.

    .venv/Scripts/python scripts/benchmark.py

Reads  scripts/queries.json   (20 labelled queries, 5 of them Hinglish/Hindi)
Reads  corpus/data/embeddings/jina-embeddings-v3/vectors.npy  (task 2 output)
Reads  corpus/data/embeddings/BAAI__bge-m3/vectors.npy        (created by this script)

Outputs
  - a results table printed to stdout (recall@1, @3, @5, MRR, avg embed latency, estimated cost)
  - corpus/data/embeddings/benchmark_results.json (for the note)

Task 6 (3 queries where both models fail) is at the bottom of the output.
Task 7 (near-duplicate detection) is in detect_near_duplicates.py.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "corpus" / "data"
QUERIES_FILE = Path(__file__).resolve().parent / "queries.json"

JINA_MODEL = "jina-embeddings-v3"
JINA_URL = "https://api.jina.ai/v1/embeddings"
JINA_DIMENSIONS = 1024
JINA_QUERY_TASK = "retrieval.query"

# Jina free tier: $0 for first 10M tokens; after that ~$0.02 per 1M tokens
# A single query embedding is ~20-50 tokens on average.
JINA_COST_PER_1M = 0.02   # USD — set to 0 since we are on the free tier, shown for comparison

BGE_MODEL_NAME = "BAAI/bge-m3"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _read_jina_key() -> str:
    env = ROOT / ".env"
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.startswith("JINA_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("JINA_API_KEY not found in day-9/.env")


def _normalise(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1 if mat.ndim == 2 else 0, keepdims=mat.ndim == 2)
    return np.where(norms > 0, mat / norms, mat)


def load_index(model_dir: str) -> tuple[np.ndarray, list[dict]]:
    emb_dir = DATA / "embeddings" / model_dir
    vectors_path = emb_dir / "vectors.npy"
    meta_path = emb_dir / "meta.json"
    if not vectors_path.exists():
        sys.exit(f"vectors not found at {vectors_path}")
    vectors = _normalise(np.load(vectors_path))
    rows: list[dict] = json.loads(meta_path.read_text(encoding="utf-8"))["rows"]
    return vectors, rows


# ---------------------------------------------------------------------------
# Embedding: Jina API
# ---------------------------------------------------------------------------

def embed_jina(queries: list[str], key: str) -> tuple[np.ndarray, int, float]:
    """Embed all queries in one call. Returns (matrix, tokens_billed, seconds)."""
    body = {
        "model": JINA_MODEL,
        "task": JINA_QUERY_TASK,
        "dimensions": JINA_DIMENSIONS,
        "late_chunking": False,
        "truncate": False,
        "input": queries,
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    req = urllib.request.Request(JINA_URL, data=json.dumps(body).encode(), headers=headers)
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    elapsed = time.perf_counter() - t0
    matrix = np.array([d["embedding"] for d in sorted(data["data"], key=lambda x: x["index"])], dtype=np.float32)
    tokens = data.get("usage", {}).get("total_tokens", 0)
    return _normalise(matrix), tokens, elapsed


# ---------------------------------------------------------------------------
# Embedding: BGE-M3 (local, sentence-transformers)
# ---------------------------------------------------------------------------

def embed_bge(queries: list[str]) -> tuple[np.ndarray, float]:
    """Embed all queries with the local BGE-M3 model. Returns (matrix, seconds)."""
    from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]
    print("  Loading BGE-M3 (downloads ~2 GB on first run) …", flush=True)
    model = SentenceTransformer(BGE_MODEL_NAME)
    t0 = time.perf_counter()
    try:
        vecs = model.encode(queries, prompt_name="query", normalize_embeddings=True, show_progress_bar=False)
    except (TypeError, ValueError):
        vecs = model.encode(queries, normalize_embeddings=True, show_progress_bar=False)
    elapsed = time.perf_counter() - t0
    return _normalise(np.array(vecs, dtype=np.float32)), elapsed


# ---------------------------------------------------------------------------
# BGE-M3 corpus embedding (create its own vectors.npy if missing)
# ---------------------------------------------------------------------------

def build_bge_index(sections: list[dict]) -> tuple[np.ndarray, list[dict]]:
    bge_dir = DATA / "embeddings" / BGE_MODEL_NAME.replace("/", "__")
    vectors_path = bge_dir / "vectors.npy"
    meta_path = bge_dir / "meta.json"

    if vectors_path.exists():
        print(f"BGE-M3 corpus index already exists at {bge_dir.relative_to(ROOT)}")
        return load_index(BGE_MODEL_NAME.replace("/", "__"))

    print("Building BGE-M3 corpus index (this takes a few minutes) …")
    from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]
    model = SentenceTransformer(BGE_MODEL_NAME)
    texts = [" > ".join(s["heading_path"]) + "\n\n" + s["text"] for s in sections]

    # Encode in batches of 64
    batch_size = 64
    all_vecs: list[np.ndarray] = []
    t0 = time.perf_counter()
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        # For passages (corpus side) BGE-M3 does NOT use a query prefix
        try:
            vecs = model.encode(batch, prompt_name="passage", normalize_embeddings=True, show_progress_bar=False)
        except (TypeError, ValueError):
            vecs = model.encode(batch, normalize_embeddings=True, show_progress_bar=False)
        all_vecs.append(np.array(vecs, dtype=np.float32))
        done = min(i + batch_size, len(texts))
        print(f"  {done}/{len(texts)} sections embedded", end="\r", flush=True)
    elapsed = time.perf_counter() - t0
    print(f"\n  Done in {elapsed:.0f}s")

    vectors = _normalise(np.concatenate(all_vecs))
    bge_dir.mkdir(parents=True, exist_ok=True)
    np.save(vectors_path, vectors)

    # Minimal meta.json so load_index() works
    rows = [
        {"row": i, "id": s["id"], "doc_id": s["doc_id"], "source": s["source"],
         "title": s["title"], "heading_path": s["heading_path"], "words": s["words"], "licence": s["licence"]}
        for i, s in enumerate(sections)
    ]
    meta = {
        "model": BGE_MODEL_NAME, "provider": "local (sentence-transformers)",
        "task": "retrieval.passage", "dimensions": int(vectors.shape[1]),
        "dtype": "float32", "normalised_by_provider": True,
        "embedded_text": "heading path joined by ' > ', a blank line, then the section text",
        "query_task": "retrieval.query (prompt_name='query')",
        "run": {"sections": len(sections), "seconds_in_corpus_embedding": round(elapsed, 1)},
        "rows": rows,
    }
    meta_path.write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"  Saved {vectors.shape} BGE-M3 vectors to {bge_dir.relative_to(ROOT)}")
    return vectors, rows


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def top_k_search(query_vec: np.ndarray, vectors: np.ndarray, k: int = 5) -> list[int]:
    scores: np.ndarray = vectors @ query_vec
    if k >= len(scores):
        top_idx = np.arange(len(scores))
    else:
        top_idx = np.argpartition(-scores, k)[:k]
    return list(top_idx[np.argsort(-scores[top_idx])])


def hit_at_k(result_indices: list[int], correct_rows: list[int], k: int) -> bool:
    return any(i in correct_rows for i in result_indices[:k])


def reciprocal_rank(result_indices: list[int], correct_rows: list[int]) -> float:
    for rank, i in enumerate(result_indices, start=1):
        if i in correct_rows:
            return 1.0 / rank
    return 0.0


def find_correct_rows(rows: list[dict], query: dict) -> list[int]:
    """Return all row indices whose source or title matches the query's correct answer."""
    # Document-level rule (decided before re-running): a result is correct when it is a section of
    # one of the query's `correct_docs`. Exact document ids, no title matching, and NO fallback to a
    # whole source (the old fallback made 8 of the 20 queries almost impossible to miss).
    correct_docs = set(query["correct_docs"])
    matches = [i for i, row in enumerate(rows) if row["doc_id"] in correct_docs]
    if not matches:
        raise SystemExit(f"query {query['id']}: none of {sorted(correct_docs)} is in the index; fix queries.json")
    return matches


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # Load queries
    queries_data: list[dict] = json.loads(QUERIES_FILE.read_text(encoding="utf-8"))
    query_texts = [q["query"] for q in queries_data]
    hindi_ids = {q["id"] for q in queries_data if "Hindi" in q.get("notes", "") or "Hinglish" in q.get("notes", "")}

    print(f"=== Day 9 Benchmark: Jina vs BGE-M3 ===")
    print(f"Queries: {len(query_texts)} total, {len(hindi_ids)} Hindi/Hinglish\n")

    # ── Load Jina corpus index ───────────────────────────────────────────────
    print("Loading Jina corpus index …")
    jina_vectors, jina_rows = load_index("jina-embeddings-v3")
    print(f"  Jina: {jina_vectors.shape}\n")

    # ── Load sections for BGE-M3 ────────────────────────────────────────────
    sections: list[dict] = json.loads((DATA / "sections.json").read_text(encoding="utf-8"))

    # ── Build BGE-M3 corpus index (or load if already built) ────────────────
    print("Loading / building BGE-M3 corpus index …")
    bge_vectors, bge_rows = build_bge_index(sections)
    print(f"  BGE-M3: {bge_vectors.shape}\n")

    # ── Embed all queries: Jina ──────────────────────────────────────────────
    print("Embedding 20 queries with Jina …")
    key = _read_jina_key()
    jina_q_vecs, jina_tokens, jina_embed_s = embed_jina(query_texts, key)
    print(f"  Done: {jina_tokens} tokens, {jina_embed_s:.2f}s total ({jina_embed_s / len(query_texts) * 1000:.0f} ms/query avg)\n")

    # ── Embed all queries: BGE-M3 ────────────────────────────────────────────
    print("Embedding 20 queries with BGE-M3 (local) …")
    bge_q_vecs, bge_embed_s = embed_bge(query_texts)
    print(f"  Done: {bge_embed_s:.2f}s total ({bge_embed_s / len(query_texts) * 1000:.0f} ms/query avg)\n")

    # ── Score both ──────────────────────────────────────────────────────────
    results: list[dict] = []
    jina_hits = {1: 0, 3: 0, 5: 0}
    bge_hits  = {1: 0, 3: 0, 5: 0}
    jina_rr_total = 0.0
    bge_rr_total  = 0.0

    for i, q in enumerate(queries_data):
        is_hindi = q["id"] in hindi_ids
        jina_top = top_k_search(jina_q_vecs[i], jina_vectors, k=10)
        bge_top  = top_k_search(bge_q_vecs[i],  bge_vectors,  k=10)

        correct_jina = find_correct_rows(jina_rows, q)
        correct_bge  = find_correct_rows(bge_rows,  q)
        # Use jina row mapping for both (same sections.json order)
        correct = correct_jina if correct_jina else correct_bge

        jh1 = hit_at_k(jina_top, correct, 1)
        jh3 = hit_at_k(jina_top, correct, 3)
        jh5 = hit_at_k(jina_top, correct, 5)
        bh1 = hit_at_k(bge_top, correct, 1)
        bh3 = hit_at_k(bge_top, correct, 3)
        bh5 = hit_at_k(bge_top, correct, 5)

        jrr = reciprocal_rank(jina_top, correct)
        brr = reciprocal_rank(bge_top, correct)

        for k_val, hit in [(1, jh1), (3, jh3), (5, jh5)]:
            if hit:
                jina_hits[k_val] += 1
        for k_val, hit in [(1, bh1), (3, bh3), (5, bh5)]:
            if hit:
                bge_hits[k_val] += 1
        jina_rr_total += jrr
        bge_rr_total  += brr

        results.append({
            "id": q["id"],
            "query": q["query"],
            "hindi": is_hindi,
            "correct_rows_count": len(correct),
            "jina": {"hit@1": jh1, "hit@3": jh3, "hit@5": jh5, "rr": round(jrr, 4), "top5": jina_top[:5]},
            "bge":  {"hit@1": bh1, "hit@3": bh3, "hit@5": bh5, "rr": round(brr, 4), "top5": bge_top[:5]},
        })

    n = len(queries_data)
    n_hindi = len(hindi_ids)
    n_en = n - n_hindi

    # ── Print results table ──────────────────────────────────────────────────
    def pct(hits: int, total: int) -> str:
        return f"{hits}/{total} ({100 * hits / total:.0f}%)"

    print("=" * 60)
    print("RESULTS (all 20 queries)")
    print("=" * 60)
    print(f"{'Metric':<25} {'Jina':<15} {'BGE-M3':<15}")
    print("-" * 55)
    for k_val in [1, 3, 5]:
        print(f"  Recall@{k_val:<18} {pct(jina_hits[k_val], n):<15} {pct(bge_hits[k_val], n):<15}")
    print(f"  MRR                    {jina_rr_total / n:<15.4f} {bge_rr_total / n:<15.4f}")
    print(f"  Embed latency (20 q)   {jina_embed_s * 1000:.0f} ms (API)   {bge_embed_s * 1000:.0f} ms (local)")
    print(f"  Tokens billed          {jina_tokens:<15} {'0 (local)':<15}")
    jina_cost = jina_tokens / 1_000_000 * JINA_COST_PER_1M
    print(f"  Estimated cost (USD)   ${jina_cost:<14.4f} $0.0000 (local)")

    # Hindi-only subset
    hindi_results = [r for r in results if r["hindi"]]
    if hindi_results:
        jh5_hindi = sum(1 for r in hindi_results if r["jina"]["hit@5"])
        bh5_hindi = sum(1 for r in hindi_results if r["bge"]["hit@5"])
        print()
        print(f"Hindi/Hinglish subset ({n_hindi} queries):")
        print(f"  Recall@5  Jina: {pct(jh5_hindi, n_hindi)}   BGE-M3: {pct(bh5_hindi, n_hindi)}")

    # ── Task 6: 3 queries where BOTH models failed at @5 ──────────────────
    both_fail = [r for r in results if not r["jina"]["hit@5"] and not r["bge"]["hit@5"]]
    print()
    print("=" * 60)
    print(f"TASK 6 — Queries where BOTH models failed @5 ({len(both_fail)} found):")
    print("=" * 60)
    for r in both_fail[:6]:
        print(f"  Q{r['id']:02d}: {r['query']!r}")
        print(f"       correct rows in index: {r['correct_rows_count']}")
        if r["correct_rows_count"] == 0:
            print("       ⚠ No matching rows found — check correct_source/correct_title in queries.json")
        print()

    # ── Save results ────────────────────────────────────────────────────────
    out = {
        "summary": {
            "jina": {f"recall@{k}": jina_hits[k] / n for k in [1, 3, 5]} | {"mrr": jina_rr_total / n, "embed_ms_total": round(jina_embed_s * 1000), "tokens": jina_tokens},
            "bge":  {f"recall@{k}": bge_hits[k]  / n for k in [1, 3, 5]} | {"mrr": bge_rr_total  / n, "embed_ms_total": round(bge_embed_s * 1000), "tokens": 0},
        },
        "per_query": results,
        "both_fail_at_5": [r["id"] for r in both_fail],
    }
    out_path = DATA / "embeddings" / "benchmark_results.json"
    def numpy_to_python(value):  # row numbers from argpartition are numpy ints, which json cannot write
        if isinstance(value, np.integer):
            return int(value)
        if isinstance(value, np.floating):
            return float(value)
        if isinstance(value, np.ndarray):
            return value.tolist()
        raise TypeError(f"cannot write {type(value).__name__} as JSON")

    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False, default=numpy_to_python), encoding="utf-8")
    print(f"Full results saved to {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
