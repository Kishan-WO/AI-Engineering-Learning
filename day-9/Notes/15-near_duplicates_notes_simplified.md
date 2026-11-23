# Explaining the near-duplicate detection note

This note describes a script that finds pairs of sections in your corpus that are almost the same, using the Jina vectors from `embed_jina.py`.

---

## 1. The core idea

Each section is a vector of 1024 numbers. Two sections with similar meaning have vectors pointing in a similar direction. **Cosine similarity** measures that, from 1.0 (same direction) down toward 0 (unrelated).

Because the Jina vectors have length 1 (the `normalised` check in `embed_jina.py`), the cosine is just a dot product:

```python
cosine = vector_a @ vector_b
```

The script says: "if the cosine of two sections is at or above 0.97, call them a near-duplicate pair."

---

## 2. What the script does

It compares every section with every section after it. With 2,097 sections, that is a 2,097 x 2,097 table of scores. It does this in **blocks of 512 rows** instead of building the whole table at once:

```
rows 0-511    vs  all later rows
rows 512-1023 vs  all later rows
...
```

That is a habit that scales. Here the full table would only be about 17 MB, so it would fit, but with a much bigger corpus it would not.

"After" matters because comparing A with B is the same as comparing B with A. You only want each pair once, and you don't want a section compared with itself (that is always 1.0).

---

## 3. The bug

The first version found 28 pairs, but only 15 were really different. 13 pairs were reported twice, as (A, B) and as (B, A).

The reason: when A and B were both inside the same block of 512 rows, the block was compared against itself in full. A vs B and B vs A both passed the threshold, so both were written out.

The fix: start each block at its own first row, and mask out every cell where the second row is not after the first. Only the upper triangle of the table survives:

```
      A  B  C
  A   x  ✓  ✓
  B   x  x  ✓      ✓ = kept, x = masked
  C   x  x  x
```

Notice that 28 - 13 = 15. The bug only affected same-block pairs, so only those were doubled.

The author then **tested the fix** against the simple method (`V @ V.T`, take the upper triangle) with different thresholds and block sizes. The results were identical every time, which is strong evidence the blocked version is correct.

---

## 4. The 15 pairs found

The table in the note shows what kinds of sections matched. They are all of this type:

- **Tables with the same layout:** pages of one electrode-potential table, or result tables of the same paper.
- **Documentation entries with the same template:** Pydantic error pages like `date_past` / `datetime_past`, or `less_than` / `less_than_equal`.
- **A real repeat:** the FastAPI `fastapi dev` passage appears in two pages.

13 of the 15 pairs are inside one page, and only 2 are across pages.

---

## 5. How the threshold changes the result

| Threshold | Pairs |
|---|---|
| 0.99 | 2 |
| 0.97 | 15 |
| 0.90 | 155 |
| 0.85 | 689 |

Lowering the threshold lets more pairs through. The growth is fast below 0.93, so the choice matters a lot.

Two findings follow from the columns:

- Nearly all pairs are **inside one page**. That is natural: a page uses one vocabulary and one style.
- Almost no pairs are **across the four sources**, so the sources do not copy each other.

The author is honest that **0.97 was chosen because 15 pairs is a readable number**, not because it was tested against a ground truth of what is truly duplicate.

---

## 6. The important observation

The author also compared the actual text of the pairs (shared 5-word sequences). The result:

> A high cosine often means "same layout, different content", not "same text".

For example, the top three pairs (cosine 0.997 to 0.989) share only about 10% of their text. They are table pages with the same columns and similar numbers, so the embedding sees them as very alike. Meanwhile the real repeat, the `fastapi dev` passage, shares 100% of its text but has a cosine of only 0.98.

So **a similarity threshold alone cannot tell a real duplicate from a same-template page**. The author did not add the text check to the script, because the task only asked for a threshold, and says so openly.

---

## 7. Limits

- The threshold is a judgement call, and most of the 15 pairs were not checked one by one.
- Only Jina vectors were used, not BGE-M3.
- Sections are 40 to 1,500 words, so a repeated paragraph inside a larger section can be missed (its vector is dominated by the rest of the section).

---

## 8. Answers to the quick-check questions

1. **Why 28 pairs when there were 15?** Pairs inside the same 512-row block were counted in both directions, (A, B) and (B, A). 13 pairs were doubled, and 15 + 13 = 28.
2. **Why can a cosine of 0.99 still mean different text?** Embeddings capture overall meaning and structure, not exact wording. Two table pages with the same columns and similar numbers look almost identical to the model, yet share very few actual words.
3. **What does it say that almost no pairs are across sources?** The four sources (chemistry book, paper, Pydantic docs, FastAPI docs) are about different things and written separately, so they do not repeat each other. The near-duplicates come from structure inside a single source.
