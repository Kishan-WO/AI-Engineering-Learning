# Day 9 task 2: embed the corpus with one API model, in batches, and store the vectors

Built: `scripts/embed_jina.py`. Result files: `results/jina-embeddings-v3_meta.json` (settings, one entry per row, per-batch log). The vectors themselves (`vectors.npy`, 8.6 MB) are not committed; `python scripts/embed_jina.py` rebuilds them from `corpus/data/sections.json`.

## 1. Which model, and why
- **Choice:** Jina `jina-embeddings-v3`, 1,024 dimensions. First choice was Gemini, but its free tier allows **1,000 texts a day per model** (100 requests and 30,000 tokens a minute, and each text counts as one request, which I confirmed on the dashboard: 6 texts in 5 calls showed as 6 requests). The corpus has 2,097 sections, so it would have needed three days.
- **Jina's free key:** 10M free tokens and, per the rate-limit table, 100 requests and 100,000 tokens a minute. The other options I looked at are in the learning notes; AWS Titan was not tried.
- **Settings:** `task=retrieval.passage` for the corpus (the queries use `retrieval.query`), `late_chunking=false`, `truncate=false` (a too-long input is an error, not a silent cut), 1,024 dimensions, float32.
- **What is embedded for a section:** the heading path joined by ` > `, a blank line, then the section text. The open model got exactly the same text.

## 2. How the script works
1. Reads `sections.json` and the key from `day-9/.env` (never printed).
2. Makes batches of at most 32 texts or about 12,000 estimated tokens: **116 batches** for 2,097 sections.
3. Keeps its own count of requests and tokens over the last 60 seconds and stays under 90 requests and 90,000 tokens a minute (Jina's limits are 100 and 100,000). It uses an estimate before a call and Jina's real count after it.
4. Retries a 429 or a server error with growing waits (up to 6 attempts). Any other 4xx stops the run.
5. Saves each batch as `batch_NNNN.npy` plus a small JSON (section ids, text hashes, tokens) as soon as it returns. A second run reuses a saved batch only if the ids and hashes still match.
6. Joins the batches into `vectors.npy` (2097 x 1024, float32) and writes `meta.json`.

## 3. The result (from `meta.json`)
| | |
|---|---|
| Sections embedded | 2,097 (234 documents) |
| Batches | 116 |
| Tokens billed by Jina | **1,270,018** (my estimate was 1,170,121, so 8.5% low) |
| Price | free tier (10M tokens per new key), $0 |
| Time inside API calls | 235 s (median batch 1.58 s, slowest 16.4 s) |
| Retries | 2 |
| Whole run | 910 s, of which 673 s was my own pacing waiting for the 90,000-tokens-a-minute budget |
| Vector length | 1.0 for every row (Jina returns normalised vectors; min 1.0, max 1.0) |
| Shape and size | (2097, 1024), float32, 8.6 MB |

- The run took about 15 minutes, mostly waiting on the limit I set. A higher budget (up to 100,000) would have saved a little; the API calls themselves took under 4 minutes.
- **A trial run first:** `--limit 64` embedded 64 sections (18,257 tokens, 2 batches, 3 s). A second run of the same trial reused both batches and made no API call, which checks the resume logic.

## 4. What the trial run found
- Row 0 of the trial was `fastapi-docs/_llm-test.md`, a test file for FastAPI's translation tool, not documentation. I made the loader skip files whose name starts with an underscore, re-ran it (235 to 234 documents, 2,109 to 2,097 sections) and deleted the trial output before the full run.
- `meta.json` timings had been overwritten to 0 s by the second trial run. They are now computed from the per-batch log, so a run that was stopped and continued still reports correct totals.

## 5. The open model
BGE-M3 (`BAAI/bge-m3`, local, sentence-transformers) embedded the same 2,097 texts: **12,541 s (3.5 hours) on CPU**, 1,024 dimensions, also normalised. It was built by `scripts/benchmark.py` the first time that script ran; its metadata is in `results/bge-m3_meta.json`.

## 6. Limits
- The token count of my estimate is rough (1.35 tokens per word, or characters / 4, whichever is larger). It was low by 8.5%, and the 10% safety margin in the budget absorbed that.
- One run per model. I did not measure how much the time changes with a bigger budget.
- The Jina price is free-tier; I did not check a paid price.

## Quick check
- Why was Gemini's free tier not enough for this corpus in one day?
- Why does the script keep its own token count when Jina returns the real one?
- What makes a saved batch safe to reuse on the next run?
