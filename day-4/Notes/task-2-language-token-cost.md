# Task 2: English, Hindi and Hinglish: token counts and the cost for 1 million messages

Task: compare token counts for the same paragraph in English, Hindi and Hinglish, and estimate the cost difference for 1 million messages.

Script: `day-4/tasks/task2_language_cost.py` (reuses the tokenizers from `task1_token_counts.py`).
Input: the three paragraphs in `day-4/data/my_text.md` (headings `### English`, `### Hindi`, `### Hinglish`). They say the same thing: a chatbot forgets because the whole conversation is re-sent on every call.

```bash
uv run python tasks/task2_language_cost.py
uv run python tasks/task2_language_cost.py --input-price 2.5 --output-price 10 --reply-ratio 1.5
```

## 1. How the cost is estimated
- **One message = one paragraph.** The paragraph is sent as input.
- **The reply** is assumed to be in the same language and `reply_ratio` times as long (default 1.0).
- **Prices are per million tokens**, one for input and one for output.

```
cost for N messages = N × tokens × (input_price + reply_ratio × output_price) ÷ 1,000,000
```
With N = 1,000,000 the millions cancel: **cost in USD = tokens × (input_price + reply_ratio × output_price)**.

**The prices in the script are round example numbers (1.0 for input, 4.0 for output, USD per million tokens), not a real quote.** Provider prices change every few months, so the real number must come from the provider's current price page. What does not change with the price is the *ratio* between the languages.

## 2. Token counts (measured)
| Language | Characters | cl100k | o200k | Qwen2.5 |
|---|---|---|---|---|
| English | 231 | 47 | 45 | 47 |
| Hindi | 220 | 241 | 68 | 218 |
| Hinglish | 257 | 88 | 74 | 88 |

Ratio against English:
| Language | cl100k | o200k | Qwen2.5 |
|---|---|---|---|
| Hindi | 5.13x | 1.51x | 4.64x |
| Hinglish | 1.87x | 1.64x | 1.87x |

## 3. Cost for 1,000,000 messages, at the example prices
Input 1.0 and output 4.0 USD per million tokens, reply the same length as the message:

| Language | cl100k | o200k | Qwen2.5 |
|---|---|---|---|
| English | 235 | 225 | 235 |
| Hindi | 1,205 | 340 | 1,090 |
| Hinglish | 440 | 370 | 440 |

Extra cost compared with English:
| Language | cl100k | o200k | Qwen2.5 |
|---|---|---|---|
| Hindi | +970 | +115 | +855 |
| Hinglish | +205 | +145 | +205 |

Check of the arithmetic: English with `cl100k` is 47 × (1 + 1×4) = 235; Hindi is 241 × 5 = 1,205.

With other settings (input 2.5, output 10, reply 1.5× longer) the `o200k` English cost is 45 × (2.5 + 1.5×10) = 788, Hindi is 1,190 and Hinglish is 1,295. The ratios stay the same.

## 4. What it means
- **The same message in Hindi script costs from 1.5 to 5 times the English cost**, depending on the tokeniser. With the older encoding (`cl100k`) and with Qwen it is more than 4.5 times; with the newer `o200k` it is about 1.5 times.
- **Hinglish (Hindi in Roman letters) is cheaper than Hindi script on the older tokenisers** (1.87x against 5.13x), but it is **not** cheaper on the newer one (1.64x against 1.51x), where Hindi script is already efficient. So "write Hinglish to save tokens" is not a rule; it depends on the tokeniser.
- **The tokeniser matters more than the language**: the same Hindi paragraph is 241 tokens with `cl100k` and 68 with `o200k`.
- **Output tokens usually cost more than input tokens**, and a reply in Hindi is as expensive to generate as the question, so the language multiplier applies to both sides of the bill.
- **Fewer tokens also means faster and more room**: lower latency and more text fitting in the context window.

## 5. Limits of this estimate
- One paragraph is one sample; other texts give other ratios.
- The reply length is an assumption, set with `--reply-ratio`.
- The prices are placeholders.
- These tokenisers are OpenAI's two encodings and an open Qwen model. A provider such as Anthropic or Google has its own tokeniser, so the real count for that model must come from its own token-count tool.
- Extra costs (cached input, thinking tokens, images) are not included.

## Quick check
- Why does the ratio against English not depend on the price?
- Why is the same Hindi paragraph 241 tokens in one tokeniser and 68 in another?
- When is Hinglish cheaper than Hindi script, and when is it not?
- What happens to the cost if the replies are 1.5 times as long?
- Why must the real prices come from the provider's current price page?
