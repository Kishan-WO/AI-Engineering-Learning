# Why truncated vectors must be normalised again

**The sentence from note 6 (Dimensions):** "Re-normalising after truncation is required. The first 512 numbers of a unit vector do not have length 1 any more, and a dot product on them is no longer a cosine."

## The short answer
A unit vector has length 1. That is why a plain dot product on it gives the cosine similarity. Truncating a vector to its first 512 numbers breaks the length 1 property, so the dot product stops being a cosine. Dividing the truncated vector by its own length restores it. That step is re-normalising.

## 1. Why the dot product equals the cosine
```
cosine(a, b) = (a . b) / (|a| x |b|)
```
When both lengths are 1, the bottom is 1 x 1 = 1, so `cosine = a . b`. This is why the search normalises once and then does a single `docs @ q`.

## 2. What truncation does to the length
Length is `sqrt(sum of squares of all the numbers)`. If I keep only the first 512 of 1,536 numbers, I drop the squares of the other 1,024. The sum is smaller, so the length is below 1.

Example: the vector `[0.5, 0.5, 0.5, 0.5]` has length 1, because 4 x 0.25 = 1. Keep the first two numbers, `[0.5, 0.5]`, and the length is `sqrt(0.5) = 0.707`.

## 3. A small example where it changes the ranking
4 dimensions, and I keep the first 2:
```
query q = [0.6, 0.8, 0,   0    ]   length 1
doc D1  = [0.6, 0.8, 0,   0    ]   length 1
doc D2  = [0.3, 0.4, 0.5, 0.707]   length 1
```
After truncating, the kept parts of D1 and D2 point in exactly the same direction, so both should score 1.0:

| Truncated doc | Plain dot product with `[0.6, 0.8]` | After re-normalising |
|---|---|---|
| D1 = `[0.6, 0.8]` (length 1) | 1.0 | 1.0 |
| D2 = `[0.3, 0.4]` (length 0.5) | **0.5** | **1.0** |

Without re-normalising, D2 scores half as much. The cause is that D2 kept less of its total length in those first two numbers, so its truncated vector is shorter. The direction is the same. A score like that is a mix of angle and length, and it is no longer a cosine.

In a real search this means:
- truncated vectors with little weight in their first dimensions drop down the ranking for no meaningful reason;
- any threshold, such as "above 0.9 means a near-duplicate", means something different.

## 4. The fix
```python
small = full[:, :512]                                            # truncate
small = small / np.linalg.norm(small, axis=1, keepdims=True)     # re-normalise: every row has length 1 again
```
After the second line, `small @ q` is a cosine again. The query has to be truncated to the same 512 numbers and re-normalised too.

Some APIs do both steps through a `dimensions` or `output_dimensionality` parameter. If I cut stored vectors myself, as above, I must do it.

## Quick check
- What is the length of `[0.5, 0.5]`, and what do I divide by to make it length 1?
- Why does D2 in the example score 0.5 before re-normalising when its direction is the same as the query's?
- Which two things must I truncate and re-normalise: the documents, the query, or both?
