# Day 9 task 7: detect near-duplicate sections with a similarity threshold

Script: `scripts/detect_near_duplicates.py`. Result: `results/near_duplicates_jina_0.97.json` (threshold 0.97, Jina vectors). Run: `python scripts/detect_near_duplicates.py --threshold 0.97`.

## 1. What it does
- Loads the Jina vectors (length 1, so a dot product is a cosine) and compares every section with every section after it, in blocks of 512 rows, so the full 2,097 x 2,097 matrix is never built at once.
- Keeps each pair whose cosine is at or above the threshold, and writes the pairs with their scores, ids, titles and heading paths.

## 2. A bug I fixed
The first version reported 28 pairs at 0.97, but only 15 were different: 13 pairs appeared twice (as A,B and as B,A) when both sections were in the same block of 512 rows. The comparison now starts at each block's own first row and masks every cell where the second row is not after the first. I checked the fixed script against the plain full-matrix calculation (`V @ V.T`, upper triangle) at thresholds 0.97 and 0.90 and block sizes 512, 100 and 7: the pairs were identical each time (15 and 155 pairs).

## 3. The result at threshold 0.97: 15 pairs
| Cosine | Where | What the two sections are |
|---|---|---|
| 0.9970, 0.9900, 0.9894 | Chemistry Appendix L | pages 1127-1132 of one table of electrode potentials |
| 0.9916, 0.9833, 0.9749 | paper 2407.20243 | result tables of Matryoshka-Adaptor (OpenAI small and large, unsupervised and supervised) |
| 0.9825, 0.9757, 0.9730 | Pydantic `validation_errors.md` | `date_past` / `datetime_past`, `date_future` / `datetime_future`, `date_type` / `datetime_type` |
| 0.9798, 0.9753, 0.9730 | Pydantic `validation_errors.md` | `less_than` / `less_than_equal`, `greater_than` / `greater_than_equal`, `greater_than` / `less_than` |
| 0.9788 | Pydantic `alias.md` | alias configuration / runtime settings |
| 0.9818 | FastAPI `fastapi-cli.md` / `tutorial/first-steps.md` | the `fastapi dev` passage, in two pages |
| 0.9785 | FastAPI `advanced-dependencies.md` / `dependencies-with-yield.md` | dependencies with `yield` |

13 of the 15 pairs are two sections of the same page; 2 are in two different pages.

## 4. How the number of pairs depends on the threshold
| Threshold | Pairs | Same page | Same source, other page | Across sources |
|---|---|---|---|---|
| 0.99 | 2 | 2 | 0 | 0 |
| 0.98 | 7 | 6 | 1 | 0 |
| 0.97 | 15 | 13 | 2 | 0 |
| 0.95 | 28 | 26 | 2 | 0 |
| 0.93 | 50 | 42 | 8 | 0 |
| 0.90 | 155 | 134 | 20 | 1 |
| 0.85 | 689 | 610 | 75 | 4 |

- The count grows quickly below 0.93. Nearly all pairs are inside one page, and almost none are across the four sources, so the sources do not copy each other.
- **I used 0.97** (the script's default, 15 pairs). I chose it because the count is small enough to read every pair; I did not tune it against a measure of right and wrong.

## 5. An observation, not part of the task
I also compared the text of the 689 pairs at 0.85 or above (shared 5-word sequences). It showed that a high cosine often means "same layout, different content", not "same text": the top three pairs (Appendix L, 0.997 to 0.989) share only about 10% of their text, while real repeats (for example the `fastapi dev` passage, 100% shared) are spread between 0.85 and 0.98. So the vector threshold alone does not separate real duplicates from same-template pages. I did **not** add this check to the script, since the task asks only for detection with a similarity threshold; the measurement is only in my working output.

## 6. Limits
- The threshold is a judgement. At 0.97 there are 15 pairs, none of which I have checked one by one except the ones listed above.
- It uses the Jina vectors only; I did not run the BGE-M3 vectors.
- Sections are 40 to 1,500 words, so a duplicate shorter than a section (a repeated paragraph) can be missed.

## Quick check
- Why did the first version report 28 pairs when there were 15?
- Why can two sections have a cosine of 0.99 and still not repeat each other's text?
- What does it say about the corpus that almost no pairs are across sources?
