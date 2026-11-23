"""Day 9, task 3: hand-written NumPy semantic search.

    .venv/Scripts/python scripts/search.py "how do I define a route in FastAPI?" --k 5
    .venv/Scripts/python scripts/search.py "What is TPSA?" --k 5 --model bge

Loads vectors.npy and meta.json from the embeddings folder and runs a cosine similarity
search using only NumPy (no vector-database library).

For the Jina model (default) it calls the Jina API with task=retrieval.query.
For the BGE-M3 model (--model bge) it uses the local sentence-transformers model.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "corpus" / "data"

JINA_MODEL = "jina-embeddings-v3"
JINA_URL = "https://api.jina.ai/v1/embeddings"
JINA_DIMENSIONS = 1024
JINA_QUERY_TASK = "retrieval.query"

BGE_MODEL_NAME = "BAAI/bge-m3"


# ---------------------------------------------------------------------------
# Embedding a single query
# ---------------------------------------------------------------------------

def embed_query_jina(query: str) -> np.ndarray:
    """Embed one query with Jina's API (retrieval.query task). Returns a normalised float32 (1024,)."""
    key = _read_jina_key()
    body = {
        "model": JINA_MODEL,
        "task": JINA_QUERY_TASK,
        "dimensions": JINA_DIMENSIONS,
        "late_chunking": False,
        "truncate": False,
        "input": [query],
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    req = urllib.request.Request(JINA_URL, data=json.dumps(body).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    vec = np.array(data["data"][0]["embedding"], dtype=np.float32)
    return _normalise(vec)


def embed_query_bge(query: str, model=None) -> np.ndarray:
    """Embed one query with the local BGE-M3 model. Loads the model once and reuses it."""
    if model is None:
        from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]
        model = SentenceTransformer(BGE_MODEL_NAME)
    # BGE-M3 uses a query prefix when encoding queries; sentence-transformers applies it
    # automatically when prompt_name="query" is set (available in recent versions).
    try:
        vec = model.encode(query, prompt_name="query", normalize_embeddings=True)
    except (TypeError, ValueError):
        vec = model.encode(query, normalize_embeddings=True)
    return np.array(vec, dtype=np.float32)


def _normalise(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def _read_jina_key() -> str:
    env = ROOT / ".env"
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.startswith("JINA_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("JINA_API_KEY not found in day-9/.env")


# ---------------------------------------------------------------------------
# Core search  — pure NumPy, no library
# ---------------------------------------------------------------------------

def search(
    query_vec: np.ndarray,
    vectors: np.ndarray,
    rows: list[dict],
    k: int = 5,
) -> list[dict]:
    """Return the top-k sections by cosine similarity.

    Both query_vec and vectors must already be L2-normalised so dot product == cosine.

    Steps
    -----
    1. matrix multiply: scores shape (N,) where scores[i] = dot(query, vectors[i])
    2. argpartition to get the k largest indices cheaply  (O(N), not O(N log N))
    3. sort only those k indices to put them in score order
    """
    # query_vec: (D,)   vectors: (N, D)   scores: (N,)
    scores: np.ndarray = vectors @ query_vec           # step 1

    # step 2: argpartition gives k indices in arbitrary order, with the guarantee that
    # all items at positions 0..k-1 are >= every item at positions k..N-1 (for -scores).
    if k >= len(scores):
        top_idx = np.arange(len(scores))
    else:
        top_idx = np.argpartition(-scores, k)[:k]      # cheapest top-k

    # step 3: sort just those k by descending score
    top_idx = top_idx[np.argsort(-scores[top_idx])]

    return [
        {
            "rank": rank + 1,
            "score": float(scores[idx]),
            "id": rows[idx]["id"],
            "source": rows[idx]["source"],
            "title": rows[idx]["title"],
            "heading_path": rows[idx]["heading_path"],
        }
        for rank, idx in enumerate(top_idx)
    ]


# ---------------------------------------------------------------------------
# Loader (cached after first call in the same process)
# ---------------------------------------------------------------------------

_cache: dict[str, object] = {}


def load_index(model_dir: str = "jina-embeddings-v3") -> tuple[np.ndarray, list[dict]]:
    if model_dir in _cache:
        return _cache[model_dir]  # type: ignore[return-value]
    emb_dir = DATA / "embeddings" / model_dir
    vectors_path = emb_dir / "vectors.npy"
    meta_path = emb_dir / "meta.json"
    if not vectors_path.exists():
        sys.exit(f"vectors not found at {vectors_path} — run embed_jina.py first")
    vectors = np.load(vectors_path)                       # float32, (N, D)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    rows: list[dict] = meta["rows"]
    # Normalise in case the provider did not (norms should already be 1.0 for Jina)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = np.where(norms > 0, vectors / norms, vectors)
    _cache[model_dir] = (vectors, rows)
    return vectors, rows


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Semantic search over the Day 9 corpus")
    ap.add_argument("query", help="The question or query text")
    ap.add_argument("--k", type=int, default=5, help="Number of results to return (default 5)")
    ap.add_argument(
        "--model",
        choices=["jina", "bge"],
        default="jina",
        help="Which embedding model to use for the query (default: jina)",
    )
    args = ap.parse_args()

    if args.model == "jina":
        model_dir = "jina-embeddings-v3"
        print(f"Embedding query with Jina ({JINA_MODEL}, {JINA_QUERY_TASK}) …")
        t0 = time.perf_counter()
        query_vec = embed_query_jina(args.query)
        embed_ms = (time.perf_counter() - t0) * 1000
    else:
        model_dir = BGE_MODEL_NAME.replace("/", "__")
        print(f"Embedding query with BGE-M3 (local) …")
        t0 = time.perf_counter()
        from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]
        bge = SentenceTransformer(BGE_MODEL_NAME)
        query_vec = embed_query_bge(args.query, model=bge)
        embed_ms = (time.perf_counter() - t0) * 1000

    vectors, rows = load_index(model_dir)

    t1 = time.perf_counter()
    results = search(query_vec, vectors, rows, k=args.k)
    search_ms = (time.perf_counter() - t1) * 1000

    print(f"\nQuery : {args.query!r}")
    print(f"Model : {args.model}  |  embed {embed_ms:.0f} ms  |  search {search_ms:.1f} ms\n")
    for r in results:
        path = " > ".join(r["heading_path"]) if r["heading_path"] else r["title"]
        print(f"  #{r['rank']}  score={r['score']:.4f}  [{r['source']}]  {path}")


if __name__ == "__main__":
    main()
