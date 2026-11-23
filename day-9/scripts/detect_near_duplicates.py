"""Day 9, task 7: detect near-duplicate sections using cosine similarity.

    .venv/Scripts/python scripts/detect_near_duplicates.py
    .venv/Scripts/python scripts/detect_near_duplicates.py --threshold 0.98

Loads the Jina vectors.npy and prints all pairs with cosine similarity above the threshold.
Uses only NumPy: a block-wise matrix multiply so it runs on a laptop without OOM.

Why this matters
- Near-duplicates in the corpus inflate recall scores (the same content appears twice, so
  a query that hits one also "almost hits" the other).
- They also waste embedding tokens and inflate the vector index size.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "corpus" / "data"


def find_near_duplicates(
    vectors: np.ndarray,
    rows: list[dict],
    threshold: float = 0.97,
    block_size: int = 512,
) -> list[dict]:
    """Find all (i, j) pairs with cosine similarity >= threshold.

    Block-wise so it never materialises the full N×N matrix.
    vectors must already be L2-normalised (dot product == cosine).
    """
    n = len(vectors)
    pairs: list[dict] = []

    for i_start in range(0, n, block_size):
        i_end = min(i_start + block_size, n)
        block_i = vectors[i_start:i_end]            # (block, D)
        # Compare the block with every row from its own first row to the end ...
        block_j = vectors[i_start:]                 # (n - i_start, D)
        # scores[a, b] = similarity between row (i_start + a) and row (i_start + b)
        scores = block_i @ block_j.T                # (block, n - i_start)
        # ... and keep only the cells where the second row comes AFTER the first one (b > a).
        # Without this, two rows of the same block meet twice (as A,B and as B,A) and a row
        # meets itself (score 1.0).
        columns = np.arange(scores.shape[1])[None, :]
        rows_in_block = np.arange(scores.shape[0])[:, None]
        scores[columns <= rows_in_block] = -1.0

        hit_a, hit_b = np.where(scores >= threshold)
        for a, b in zip(hit_a.tolist(), hit_b.tolist()):
            i = i_start + a
            j = i_start + b
            pairs.append({
                "i": i,
                "j": j,
                "score": round(float(scores[a, b]), 6),
                "i_id": rows[i]["id"],
                "j_id": rows[j]["id"],
                "i_source": rows[i]["source"],
                "j_source": rows[j]["source"],
                "i_title": rows[i]["title"],
                "j_title": rows[j]["title"],
                "i_heading": " > ".join(rows[i].get("heading_path", [])),
                "j_heading": " > ".join(rows[j].get("heading_path", [])),
            })

    return sorted(pairs, key=lambda p: -p["score"])


def main() -> None:
    ap = argparse.ArgumentParser(description="Detect near-duplicate sections by cosine similarity")
    ap.add_argument("--threshold", type=float, default=0.97, help="Similarity threshold (default 0.97)")
    ap.add_argument("--model-dir", default="jina-embeddings-v3", help="Embeddings subfolder")
    args = ap.parse_args()

    emb_dir = DATA / "embeddings" / args.model_dir
    vectors_path = emb_dir / "vectors.npy"
    meta_path = emb_dir / "meta.json"

    if not vectors_path.exists():
        import sys; sys.exit(f"vectors not found at {vectors_path} — run embed_jina.py first")

    print(f"Loading {vectors_path.relative_to(ROOT)} …")
    vectors = np.load(vectors_path).astype(np.float32)
    rows: list[dict] = json.loads(meta_path.read_text(encoding="utf-8"))["rows"]
    # Normalise
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = np.where(norms > 0, vectors / norms, vectors)
    print(f"  {vectors.shape[0]} sections, {vectors.shape[1]} dimensions")
    print(f"  Threshold: {args.threshold}\n")

    pairs = find_near_duplicates(vectors, rows, threshold=args.threshold)

    if not pairs:
        print(f"No near-duplicate pairs found above {args.threshold}.")
    else:
        print(f"Found {len(pairs)} near-duplicate pair(s):\n")
        for p in pairs[:30]:           # show at most 30
            print(f"  score={p['score']:.4f}")
            print(f"    A [{p['i_source']}] {p['i_title']} > {p['i_heading']}")
            print(f"    B [{p['j_source']}] {p['j_title']} > {p['j_heading']}")
            print()

    out_path = emb_dir / "near_duplicates.json"
    out_path.write_text(json.dumps({"threshold": args.threshold, "pairs": pairs}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Results saved to {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
