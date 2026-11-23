# Recall@k and MRR: how to score a search system

These metrics measure how good a search system is. You have a set of test queries, and for each one you know which document is the correct answer. The metrics tell you how often, and how high, the system finds it.

## 1. Recall@k

**Definition:** the share of queries where the correct document appears somewhere in the top k results.

```
recall@5 = (queries whose correct document is in the top 5) / (all queries)
```

**Example.** You have 10 test queries, and the system returns its top 5 results for each. The correct document shows up in the top 5 for 8 of them.

```
recall@5 = 8 / 10 = 0.8
```

So "recall@5 = 0.8" means that for 80% of queries, the right document was somewhere in the first 5 results.

**Changing k changes the strictness:**

- **recall@1** is strict: the correct document must be the very first result.
- **recall@5** is more forgiving: the first five results count.

The same system always scores at least as high at recall@5 as at recall@1.

### Hit rate vs share found

- **One correct document per query:** recall@k is "did we find it, yes or no?" averaged over queries. This is called the **hit rate**.
- **Several correct documents per query:** recall@k is the share of the correct ones found. If a query has 4 correct documents and 3 appear in the top k, that query scores 3/4 = 0.75. You then average across queries.

These definitions give different numbers, so anyone reading the results needs to know which one was used.

## 2. MRR (Mean Reciprocal Rank)

Recall@k only asks "is it in the top k?" It does not care whether the answer was 1st or 5th. MRR fixes that by rewarding higher positions.

For each query, take the rank of the correct document and compute `1 / rank`:

| Rank of correct document | Score |
|---|---|
| 1 | 1.0 |
| 2 | 0.5 |
| 3 | 0.33 |
| 5 | 0.2 |
| not found | 0 |

Then average over all queries. That average is the MRR.

**Example with 4 queries:**

| Query | Rank of correct doc | Score |
|---|---|---|
| A | 1 | 1.0 |
| B | 2 | 0.5 |
| C | 5 | 0.2 |
| D | miss | 0 |

```
MRR = (1.0 + 0.5 + 0.2 + 0) / 4 = 0.425
```

### Why MRR is useful

Imagine two models that both have recall@5 = 1.0:

- Model X puts the correct document at rank 1 every time, so MRR = 1.0.
- Model Y puts it at rank 5 every time, so MRR = 0.2.

Recall@5 sees them as identical. MRR shows that X is much better. This matters in practice, because users and LLMs in a RAG system pay most attention to the top results.

## 3. What to report

- **recall@1:** how often the answer is first (strict)
- **recall@5:** how often the answer is in the top 5 (forgiving)
- **MRR:** a single number that blends how often and how high
- **The rank of the correct document for every query:** the raw data behind all of the above

The per-query ranks matter because summary numbers hide how bad the failures are. Two systems can both have recall@5 = 0.8, but in one the 2 misses are at rank 6 (almost made it), and in the other they are at rank 400 (completely lost).

## 4. The chunking question

If documents are split into chunks before being embedded, a search returns chunks, not whole documents. You must decide what counts as "found":

- **Strict:** only the exact correct chunk counts.
- **Lenient:** any chunk from the correct document counts.

Lenient scores are always higher or equal. Choose one rule before running the benchmark and use the same rule for every model. If you pick the rule after seeing the results, you might (even unintentionally) choose the one that favors your preferred model, and models scored under different rules cannot be compared fairly.

## Summary

- **Recall@k:** is the correct document in the top k? (yes/no, averaged)
- **MRR:** how high is it? (1/rank, averaged)
- Report both, plus per-query ranks, so you see both the average and the failures.
- Define "correct" (chunk or document) up front and keep it identical across models.
