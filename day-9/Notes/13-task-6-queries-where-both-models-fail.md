# Day 9 task 6: three queries where both models fail, and why

The plan asks me to find 3 queries where both embedding models fail and explain why. The models are Jina `jina-embeddings-v3` (API) and BGE-M3 (local). The benchmark is `scripts/benchmark.py`, with the 20 queries in `scripts/queries.json` and the saved results in `corpus/data/embeddings/benchmark_results.json`.

## How I chose them
- **The rule for a hit** (decided before the final run): a result is correct when it is a section of one of the query's `correct_docs`, and a hit at k means a correct section is in the top k.
- **Only one query fails at recall@5 for both models:** Q14. That is not enough for three, so for the other two I used the queries where **both models do not rank a correct page first**. Those are not misses at recall@5, and I say so for each one.
- Queries where neither model ranked a correct page first: Q01 (Jina 3, BGE not in the top 5; not both-at-same-rank), Q03 (2, 2), Q07 (3, 3), Q13 (2, 2), Q14 (not in the top 5, both), Q16 (2, 2). I looked at Q14, Q07 and Q16.

## 1. Q14: "What is the standard enthalpy of formation of liquid water?"
Both models miss the right page in the top 5.

- **What they returned:** prose chapters on thermochemistry (chapters 5, 7, 10 and 16, about 1,000 words each) and the Appendix E water table. The right page is Appendix G.
- **Why:**
  - The answer is the row `H2O(l) –285.83 –237.1 70.0` in section #004 of Appendix G, a section of 230 words and 52 lines of numbers.
  - That section does not contain the words "enthalpy", "formation" or "water". Only the formula `H2O(l)` carries the meaning.
  - The column headings lost their symbols in the PDF text: `Substance (kJ mol–1) (kJ mol–1) (J K–1 mol–1)`. The names of the quantities are missing.
  - The section's heading is "pages 1101-1102", which says nothing about the topic. Only the first section of the appendix has the title "Standard Thermodynamic Properties".
  - So the vector of that section is "a block of numbers and formulas", and chapters that explain enthalpy of formation in words match the query better.
- **What it points to:** a table and parsing problem (the symbols are lost, the section is cut by page pairs with no topic). Day 11 is where I fix parsing and chunking.

## 2. Q07: "How does Pydantic handle field validation errors?"
The labelled page is at rank 3 for both models, so it is a hit at recall@5, but neither model ranks it first.

- **What they put first:** `errors/errors.md` (559 words) and `concepts/models.md#error-handling` (184 words), in different orders.
- **Why:**
  - The labelled page, `errors/validation_errors.md`, is a catalogue of about 97 error types. Each entry is a short section of 45 to 78 words (for example `string_too_short`).
  - The question is conceptual ("how does it handle errors"), so the two overview pages answer it better than any single catalogue entry.
- **What it points to:** partly a label problem. My label accepts only the catalogue, which may be too narrow. I did not change it after seeing the results, so that the test is not fitted to the models.

## 3. Q16 (Hinglish): "Pydantic model mein optional field kaise banate hain?"
The correct page is at rank 2 for both models, but a wrong page is first for both.

- **What they put first:** `examples/dynamic_models.md` (568 words, about creating models dynamically). BGE-M3's rank 2 is the right file but the wrong section, `models.md#dynamic-model-creation`.
- **Why:**
  - "banate hain" means "make" or "create". The models matched "create a Pydantic model", the topic of the dynamic-models page, and not "optional field".
  - The real answer is a code example in `models.md#basic-model-usage` (`Optional[int] = None`). That section has 443 words, mostly about other things, and "optional" appears once, inside code.
  - The English words in the query ("Pydantic", "model", "optional", "field") are few and generic, so the Hinglish verb carries a lot of weight.

## What the three have in common
- Both models fail in the same way on all three, so the cause is in the corpus and the sections, not in one model.
- The three causes are different: numbers without words (Q14), a topic page against a catalogue (Q07), and a verb that matches a different topic (Q16).

## Limits
- 20 queries is a small set. These three are cases I looked at closely, not a sample.
- I used what the models returned and the section texts. I did not test the explanations by changing the sections (for example adding the missing column names) and re-running.

## Quick check
- Why does a table section rank below prose chapters for a question that the table answers?
- Why was the Q07 label not widened after I saw the results?
- Which words of the Hinglish query pulled the models to the wrong page?
