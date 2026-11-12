# `chunk_words`: overlapping windows and the edge cases

The task: `chunk_words(text, size, overlap)` splits text into overlapping groups of words, handling empty text, `overlap >= size` and a short last chunk.

My questions along the way: is my assertion right, why does my test stop at the first failure, what should I update, and why was the last chunk wrong?

## 1. The idea: a sliding window
- Cut the text into words.
- Take `size` words. Move forward by **`size - overlap`** words. Take the next `size` words, and so on.
- The `overlap` words are the ones that repeat between neighbouring chunks.

```
words:   a b c d e f g h        size=3, overlap=1  → step = 2
chunk 1: a b c
chunk 2:     c d e
chunk 3:         e f g
chunk 4:             g h        (short last chunk is kept)
```

## 2. The current code
```python
def chunk_words(text: str, size: int, overlap: int = 0) -> list[str]:
    if size <= 0:
        raise ValueError(f"size must be positive, got {size}")
    if overlap < 0:
        raise ValueError(f"overlap must be non-negative, got {overlap}")
    if overlap >= size:
        raise ValueError(f"overlap ({overlap}) must be smaller than size ({size})")
    chars = text.split()
    if not chars:
        return []
    chunks = []
    for i in range(0, len(chars), size - overlap):
        chunk = chars[i:i + size]
        chunks.append(" ".join(chunk))
        if (i + size) >= len(chars):
            break
    return chunks
```
(The variable `chars` really holds words; `words` would be a clearer name.)

## 3. Why each piece exists
| Piece | Reason |
|---|---|
| `range(0, len(words), size - overlap)` | Start positions go up in steps of `size - overlap` |
| `words[i:i + size]` | A slice never fails past the end; the last chunk is just shorter |
| `" ".join(chunk)` | Turn a list of words back into text |
| `text.split()` | Splits on any whitespace and drops empty pieces, so extra spaces and newlines are cleaned |
| `if not words: return []` | Empty or blank text gives no chunks |
| `overlap >= size` is an error | The step would be 0 or negative: an endless loop, or no progress |
| The `break` | Stop once a chunk reaches the end; otherwise a leftover tail repeats words already included |

## 4. The bug I had: an off-by-one in the stop test
Case: `"a b c d e f g"`, size 3, overlap 1. The third chunk (`e f g`) already ends exactly at the end of the text.
- With `>` the loop did **not** stop there and produced one more, redundant chunk (`g`).
- With `>=` it stops: `(i + size) >= len(words)`.

An **off-by-one error** is being wrong by exactly one at a boundary (`>` vs `>=`, `<` vs `<=`, `n` vs `n-1`). The way to catch them is to test the boundaries: exact fit, one too short, one too long.

## 5. Validate before the early return
My first version returned `[]` for empty text **before** checking `size` and `overlap`. So `chunk_words("", 0, 0)` quietly returned `[]` instead of raising. Rule: **check the arguments first, then handle the special cases.**

## 6. Why `assert` stopped at the first failure
`assert` raises `AssertionError` and the script ends there, so later checks never run. To see all failures from a group, collect them:

```python
bad_cases = [(3, 3), (3, 5), (0, 0), (-1, 0), (3, -1)]
failures = []
for size, overlap in bad_cases:
    try:
        chunk_words("a b c", size, overlap)
    except ValueError:
        pass
    except Exception as e:
        failures.append(f"size={size}, overlap={overlap}: raised {type(e).__name__}, not ValueError")
    else:
        failures.append(f"size={size}, overlap={overlap}: no error raised")

assert not failures, "ValueError checks failed:\n" + "\n".join(failures)
```
(`pytest` does this natively: each test function is reported separately, and `pytest.mark.parametrize` runs one test per case.)

## 7. The cases worth testing
| Input | Expected |
|---|---|
| `"a b c d e f g h"`, 3, 1 | `["a b c", "c d e", "e f g", "g h"]` |
| `"a b c d e f g"`, 3, 1 (ends exactly) | `["a b c", "c d e", "e f g"]` |
| `"a b c d"`, 3, 0 (short tail) | `["a b c", "d"]` |
| `"hello world"`, 5, 2 (fewer words than size) | `["hello world"]` |
| `""` and `"   \n\t "` | `[]` |
| `"a   b\n\nc  d"`, 2, 0 | `["a b", "c d"]` |
| size `0`, overlap `>= size`, negative overlap | `ValueError` |

## Quick check
- What is the step size of the window?
- Why does `overlap >= size` have to be an error?
- What was the off-by-one bug, and which comparison fixed it?
- Why validate arguments before returning `[]` for empty text?
- How can a test run all its cases even when one fails?
