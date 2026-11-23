# Day 9 task 3: `search(query, k)` with only NumPy

Built: `scripts/search.py`. Example output: `results/search_examples.txt`. The index is the vectors of task 2 plus `meta.json`.

## 1. The function
```python
def search(query_vec, vectors, rows, k=5):
    scores = vectors @ query_vec                      # 1. one matrix multiply: a cosine for every section
    if k >= len(scores):
        top_idx = np.arange(len(scores))
    else:
        top_idx = np.argpartition(-scores, k)[:k]     # 2. the k best, unordered, in O(n)
    top_idx = top_idx[np.argsort(-scores[top_idx])]   # 3. sort only those k, best first
    return [{"rank", "score", "id", "source", "title", "heading_path"} for each row in top_idx]
```
- **Only NumPy:** no vector-database library and no loop over the sections. `@`, `argpartition` and `argsort` do all the work.
- **Normalised before the call, so the dot product is the cosine:** the loader divides the stored vectors by their length again when it loads them (a safeguard; Jina's are already length 1), the Jina query vector is normalised by `_normalise`, and the BGE-M3 query uses `normalize_embeddings=True`.
- **Edge case:** `argpartition` needs `k < n`, so a `k` at or above the number of sections returns all of them, sorted.
- **Row to text:** the vector file has no words. `rows[idx]` comes from `meta.json`, which has the section id, source, title and heading path; the text itself is in `sections.json`.

## 2. How a query is embedded
- **Jina:** one API call with `task=retrieval.query` (the pair of `retrieval.passage` used for the corpus).
- **BGE-M3:** the local model with the query prompt.
- The query must come from the **same** model as the index. `--model jina` and `--model bge` pick the model and the matching index folder.

## 3. Example output (real, `results/search_examples.txt`)
```
$ python scripts/search.py "How do I define a path parameter in FastAPI?" --k 5 --model jina
Model : jina  |  embed 615 ms  |  search 0.7 ms
  #1  score=0.7603  Query Parameters > Multiple path and query parameters
  #2  score=0.7543  Path Parameters and Numeric Validations
  #3  score=0.6954  Path Parameters > Path parameters containing paths
  ...
$ ... --model bge
Model : bge  |  embed 9450 ms  |  search 0.5 ms
  #1  score=0.6988  Request Body > Declare it as a parameter
  #2  score=0.6977  Query Parameters > Multiple path and query parameters
  ...
$ python scripts/search.py "FastAPI ke saath background tasks kaise chalate hain?" --k 5 --model jina
  #1  score=0.7795  Background Tasks > Caveat
  #2  score=0.7391  Background Tasks > Technical Details
  #3  score=0.6984  Background Tasks > Dependency Injection
```
The full output for both queries and both models is in `results/search_examples.txt`.

## 4. What the numbers say
- **The search itself takes 0.5 to 0.7 ms** for 2,097 vectors of 1,024 numbers. All the latency of a query is in embedding it.
- **Embedding time differs a lot:** about 0.6 s for Jina (an API call) and 9.3 to 9.5 s for BGE-M3 in this script, because the script loads the local model on every run. Inside the benchmark, where the model is already loaded, BGE-M3 takes about 55 ms per query.
- **A path-parameter question** returns, for Jina, the `Path Parameters` page at rank 3 (the "Path parameters containing paths" section); the same query is one of the two where BGE-M3 does not find the right page in the top 5 (task 5).

## 5. Limits
- Brute force is exact but compares the query with every section. That is fine for 2,097 vectors; Day 10 adds an approximate index for larger sets.
- The vectors and their row descriptions come from different files, so `meta.json` and `vectors.npy` must be rebuilt together. **The script does not check that they have the same number of rows**; a mismatch would return the wrong titles with no error. That check is missing.

## Quick check
- Why is `scores = vectors @ query_vec` the whole scoring step?
- Why `argpartition` and then a sort of only k items, not a sort of everything?
- Why must the query use the same model as the stored vectors?
