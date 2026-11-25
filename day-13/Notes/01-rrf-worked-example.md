# RRF worked example

Goes with `learning/2.fusion.md`. One calculation by hand, so that the formula stops being abstract. `k = 60`.

```
RRF(chunk) = sum over lists of  1 / (k + rank)
```

## 1. The two lists
| Rank | Vector search | Keyword search |
|---|---|---|
| 1 | A | C |
| 2 | B | A |
| 3 | C | E |
| 4 | D | F |

## 2. The terms
| Rank | `1 / (60 + rank)` |
|---|---|
| 1 | 1/61 = 0.016393 |
| 2 | 1/62 = 0.016129 |
| 3 | 1/63 = 0.015873 |
| 4 | 1/64 = 0.015625 |

## 3. The totals
| Chunk | Vector | Keyword | Total |
|---|---|---|---|
| **A** | rank 1: 0.016393 | rank 2: 0.016129 | **0.032522** |
| **C** | rank 3: 0.015873 | rank 1: 0.016393 | **0.032266** |
| B | rank 2: 0.016129 | not found | 0.016129 |
| E | not found | rank 3: 0.015873 | 0.015873 |
| D | rank 4: 0.015625 | not found | 0.015625 |
| F | not found | rank 4: 0.015625 | 0.015625 |

**Fused order: A, C, B, E, then D and F tied.**

## 4. What it shows
- **A and C are in both lists**, so they beat B and E which are in one. B was the vector search's second choice and still falls behind C, which was only its third, because C was also the keyword search's first.
- **A beats C** although C is first in the keyword list: A is first in one list and second in the other, C is third and first. The sum rewards being consistently high.
- **The gap between "in both" and "in one" (about 0.032 against 0.016) is much larger than the gap between neighbouring ranks** (about 0.0002 to 0.0003). With `k = 60`, rank matters little compared with agreement.
- **D and F tie** at 0.015625. A fixed tie rule (for example: the better of the two ranks, then the chunk ID) keeps the tests stable.

## 5. The effect of `k`
- A **small k** (for example 1) makes the top ranks count far more: 1/2 against 1/3 is a big difference, so one list's first place can outweigh agreement.
- A **large k** (for example 1,000) flattens everything: ranks hardly matter and the result approaches "count the lists".
- 60 is a robust middle that most libraries use. I do not tune it before the eval asks.

## 6. What RRF cannot see (from this example)
Suppose chunk C matched the query's exact error code and its BM25 score was ten times the score of E, while A and B were close in cosine. RRF sees only ranks, so that big gap is invisible. If exact matches matter that much, weighted fusion or a rule ("an exact-ID match goes to the top") is the answer, and the eval shows whether it is needed.

## 7. Unit test to write
The example above is a ready test: two ranked lists in, the fused order and the six totals out, with `pytest.approx`. Add cases: one empty list (the result equals the other list's order), identical lists (the order is unchanged), disjoint lists (alternating by rank), and the tie.
