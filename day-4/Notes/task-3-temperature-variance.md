# Task 3: the same prompt at temperature 0, 0.7 and 1.4, five times each

Task: call the same prompt at temperature 0, 0.7 and 1.4, five times each, and compare the variance.

Script: `day-4/tasks/task3_temperature_variance.py`. Raw answers: `results/task3_results.json` (creative prompt) and `results/task3_results_factual.json` (factual prompt).

```bash
uv run python tasks/task3_temperature_variance.py
uv run python tasks/task3_temperature_variance.py --prompt "What is the capital of Australia? Answer with one word." --results results/task3_results_factual.json
```

## 1. Setup
- **Model:** `gemma3:270m` running locally in Ollama (291 MB, runs on the CPU).
- **Endpoint:** Ollama's OpenAI-compatible API at `http://localhost:11434/v1`, called with the `openai` Python package. For a hosted model only `BASE_URL`, the api key and `MODEL` change.
- **Settings:** `temperature` as given, `max_tokens=30`, no seed. One warm-up call first, because the first call also loads the model.
- **Variance measures** per temperature, over the 5 answers:
  - **distinct answers**: how many different texts out of 5,
  - **average similarity**: the mean of `difflib.SequenceMatcher` ratios over all 10 pairs (1.00 means every answer is identical),
  - **token stdev**: how much the answer length varies.

## 2. Prompt A: creative (many good answers)
`Suggest a name for a new coffee shop in Ahmedabad. Reply with only the name.`

| Temperature | The five answers |
|---|---|
| 0 | Themed Coffee Shop (all five) |
| 0.7 | Hindustan; Theisha; Themed Coffee Shop; Themed Coffee Shop; Themed Coffee House |
| 1.4 | Akbar; **Cafe Patel**; Indo-Indian Coffee; Alam; Himalayan Brew |

| Temperature | Distinct answers | Average similarity | Average tokens | Token stdev |
|---|---|---|---|---|
| 0 | 1 of 5 | 1.00 | 5.0 | 0.0 |
| 0.7 | 4 of 5 | 0.43 | 4.8 | 0.4 |
| 1.4 | 5 of 5 | 0.20 | 5.4 | 1.2 |

## 3. Prompt B: factual (one right answer)
`What is the capital of Australia? Answer with one word.`

| Temperature | The five answers | Correct |
|---|---|---|
| 0 | Canberra ×5 | 5 of 5 |
| 0.7 | Sydney; Canberra ×4 | 4 of 5 |
| 1.4 | Sydney; Canes Island; New Southport; Canberra ×2 | 2 of 5 |

| Temperature | Distinct answers | Average similarity | Average tokens | Token stdev |
|---|---|---|---|---|
| 0 | 1 of 5 | 1.00 | 3.0 | 0.0 |
| 0.7 | 2 of 5 | 0.71 | 3.0 | 0.6 |
| 1.4 | 4 of 5 | 0.34 | 4.2 | 0.7 |

## 4. What I see
- **Temperature 0 gave the same answer all five times** on both prompts (1 distinct answer, similarity 1.00, zero length variation). It is the most repeatable setting.
- **Variance rises with temperature**: on the creative prompt, distinct answers go 1 → 4 → 5 and similarity goes 1.00 → 0.43 → 0.20.
- **For a task with one right answer, higher temperature means more wrong answers.** At 0.7 one answer was wrong (Sydney); at 1.4 three of five were wrong, including invented places (Canes Island, New Southport). Randomness does not add knowledge, it only lets unlikely tokens through.
- **For a creative task, variance is the point.** Temperature 0 gave the dull "Themed Coffee Shop" five times; 1.4 gave five different names, though some stray from the instruction (`**Cafe Patel**` has Markdown stars, and "Indo-Indian Coffee" is odd).
- **Answer length also varies more** at high temperature (token stdev 0.0 → 0.4 → 1.2 on prompt A).
- **Speed did not change** with temperature (about 0.3 seconds per call here).

So: **low temperature for extraction and factual answers, higher temperature when variety is wanted.**

## 5. Cautions
- Only 5 calls per temperature and one run: the exact numbers change when I run it again at 0.7 and 1.4. The pattern (more variety, more errors as temperature rises) is the lesson.
- `gemma3:270m` is a tiny model; a large model makes fewer mistakes at the same temperature.
- Temperature 0 was fully repeatable here, but that is not guaranteed in general (parallel hardware and batching can change a result slightly).
- Some hosted providers limit temperature to 1, so 1.4 can be rejected there; check the provider's documented range.
- Ollama ignores the api key but the client needs one, hence `api_key="ollama"`.

## Quick check
- What does temperature 0 do, and what did five calls at 0 show?
- Why did the factual prompt get worse answers at 1.4?
- Which temperature would I choose for data extraction, and which for name suggestions?
- Why can't I trust exact numbers from five calls?
