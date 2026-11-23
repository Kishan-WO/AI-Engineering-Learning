# Top-k with NumPy: argsort vs argpartition

This note explains how to find the indices of the `k` highest scores, best first. This is the last step of a vector search, where `scores` holds the similarity between the query and every document.

Example used throughout:

```python
scores = np.array([0.2, 0.9, 0.1, 0.7, 0.5, 0.8])   # n = 6 documents
k = 3
```

The correct answer is `[1, 5, 3]`, because those positions hold 0.9, 0.8 and 0.7, in that order.

## Why the minus sign?

`np.argsort` and `np.argpartition` work in ascending order (smallest first), but we want the largest scores. Negating the scores flips the order, so the biggest score becomes the smallest number and comes first.

```python
-scores  ->  [-0.2, -0.9, -0.1, -0.7, -0.5, -0.8]
```

## Method 1: full sort, then cut

```python
order = np.argsort(-scores)[:k]
```

`np.argsort` sorts all n items and returns their indices in sorted order, not the values.

```python
np.argsort(-scores)      # [1, 5, 3, 4, 0, 2]
np.argsort(-scores)[:k]  # [1, 5, 3]
```

It fully sorts all n items and then keeps only the first k, so it does more work than needed. Cost: **O(n log n)**.

## Method 2: argpartition (top k, unordered)

```python
part = np.argpartition(-scores, k)[:k]
```

This line has three pieces:

1. `-scores` flips the sign so the best scores become the smallest values.
2. `np.argpartition(-scores, k)` rearranges the indices so the k smallest values of `-scores` (the k best scores) are in the first k positions. It does not sort inside either group.
3. `[:k]` keeps only those first k indices.

For the example, the result could be `[3, 1, 5]`. These point to 0.7, 0.9 and 0.8, which are the right three documents, but not in ranked order. Because it never orders anything precisely, it is cheaper. Cost: **O(n)** on average.

## Method 3: sort only the k winners

```python
order = part[np.argsort(-scores[part])]
```

This fixes the missing order from Method 2. With `part = [3, 1, 5]`:

1. `scores[part]` gives `[0.7, 0.9, 0.8]`.
2. `-scores[part]` gives `[-0.7, -0.9, -0.8]`.
3. `np.argsort(...)` gives `[1, 2, 0]`. These are positions inside `part`, not document ids.
4. `part[[1, 2, 0]]` converts those positions back to document ids: `[1, 5, 3]`.

Sorting only k items is cheap, **O(k log k)**.

## How they fit together

| Approach | Calls used | Work done | Cost |
|---|---|---|---|
| A: sort everything, then cut | Method 1 | Sort all n | O(n log n) |
| B: partition, then sort the winners | Methods 2 + 3 | Partition all n, sort only k | O(n + k log k), effectively O(n) |

Both approaches give the same final answer, `[1, 5, 3]`.

## When to use which

- **Small corpus** (thousands of documents): the difference is invisible, so use Approach A for readability.
- **Large corpus** (millions of vectors, many queries): Approach B can be several times faster, and the saving repeats on every query.

## Two things to watch

- `np.argpartition(-scores, k)` requires `k < n`. If `k >= n` it raises an error, so use `k = min(k, n - 1)` or fall back to a full sort.
- With tied scores, the two approaches may return tied items in different orders. Both are valid.
