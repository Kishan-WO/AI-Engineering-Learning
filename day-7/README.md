# Day 7: Prompt engineering

**Build target (from the plan):** a prompt registry, plus a measured before/after prompt improvement in `ai-service`.

Today starts with the learning notes (written first, as on Day 5 and 6). The build and the results come after.

## Layout
```
day-7/
  README.md      this index
  learning/      the concept notes (written first)
  Notes/         what was built and the measured results (after the build)
```

## Learning notes (`learning/`)
They follow the plan's "Learn" sections, in order:
| Note | Plan section | What it covers |
|---|---|---|
| `1.prompt-anatomy.md` | Prompt anatomy | the five parts, being specific, delimiting input with tags, long documents first and the question last, a reusable skeleton |
| `2.techniques.md` | Techniques | zero-shot, few-shot (example choice and order), chain-of-thought and reasoning models, ReAct, decomposition, self-consistency, and when to use which |
| `3.system-prompting.md` | System prompting | behaviour, persona, refusals and missing information, why guardrails are never the only defence, system vs user prompt |
| `4.constraining-output.md` | Constraining output | schemas, enums and fixed labels, "answer only from the context", length control, output language control, a full classifier prompt |
| `5.prompts-as-code.md` | Prompts as code | files instead of f-strings, `prompts/<name>/vN.md`, templates, logging the prompt version, structuring for the cache |
| `6.measuring-prompts.md` | Measuring prompts | a 20 to 30 case labelled test set, exact match / field accuracy / rubric, one change at a time, how big a difference is real, the decision record |

## Tasks (from the plan)
| Task | What | Status |
|---|---|---|
| **1** | Prompt registry: `prompts/<name>/v1.md`, `v2.md`, loaded by name and version; the version stored in the request logs | done |
| **2** | Move every prompt in `ai-service` into the registry | done: `/extract` (3 prompts) and `/chat` (2 prompts) |
| **3** | Choose one prompt to improve (`/extract`, or a classifier: admission / fees / schedule / academic / complaint) | the classifier |
| **4** | Build a 30-case labelled test set | done (a hard set plus an independent easy set) |
| **5** | Measure v1 zero-shot, v2 clear structure and constraints, v3 few-shot, v4 chain-of-thought or a reasoning model: accuracy, tokens and cost for each | done, two runs |
| **6** | Keep the cheapest version within 2 points of the best; record the decision in `decisions.md` | v2 (`decisions.md` 42) |
| Notes | A personal prompt-writing checklist | done: `Notes/prompt-writing-checklist.md` |

## What Day 5 and 6 already give me
- **The prompts to move (task 2):** the `/extract` system prompt, its `<message>` wrapper and its repair message (all in `extract_service.py`), the short `CHAT_SYSTEM_PROMPT` in `config.py`, and the long `prompts/chat_system.md`.
- **The measuring tools:** token counts and `cost_usd` per call in the `llm_calls` table (Day 6), outcome categories, and a runner that scores answers against what each input should give (`scripts/run_messy_inputs.py`).
- **A model for the test set:** `scripts/messy_inputs.py`, where each input carries what a correct answer looks like.
- **The place to log the prompt version:** `CallContext` and the `llm_calls` row, which already carry the request id, tenant and feature.
- **The lesson to carry on:** valid is not correct (Day 5 and 6), so the score must be checked against labels, not read by eye.

## Two honest notes for the measuring step
- On a 30-case set **one case is 3.3 points**, so "within 2 points of the best" means "the same or one case worse"; the decision should say so (see `6.measuring-prompts.md`).
- The classifier is the easier choice to score (exact match on a fixed label set); `/extract` has more fields and needs field-level scoring. I will pick one when the build starts.

## Results
See `Notes/tasks-1-6-prompt-registry-and-measured-prompts.md` (tables, the four mistakes of v1, the limits) and `Notes/prompt-writing-checklist.md`.
