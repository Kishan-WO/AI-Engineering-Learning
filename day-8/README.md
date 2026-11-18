# Day 8: LLM orchestration

**Build target (from the plan):** an intent router, and the same flow built in the plain SDK and in a framework.

Today starts with the learning notes (written first, as on earlier days). The build and the results come after.

## Layout
```
day-8/
  README.md      this index
  learning/      the concept notes (written first)
  Notes/         what was built and the measured results (after the build)
```

## Learning notes (`learning/`)
They follow the plan's "Learn" sections, in order:
| Note | Plan section | What it covers |
|---|---|---|
| `1.chains.md` | Chains | deterministic A, B, C pipelines, passing structured output between steps, validation gates, where chains fail (error propagation, compounding accuracy, latency and cost) |
| `2.routing.md` | Routing | a small model classifies and a large model handles the hard cases, rule-based routing first, confidence thresholds and fallback, measuring the router and its cost |
| `3.parallel-execution.md` | Parallel execution | `asyncio.gather` fan-out, map-reduce over many documents, concurrency limits, partial failures (`return_exceptions`, `TaskGroup`) |
| `4.graphs-and-state-machines.md` | Graphs and state machines | why some flows need branches, cycles, retries and pauses; LangGraph concepts (state, nodes, edges, conditional edges, checkpointer, interrupts); streaming steps |
| `5.framework-trade-offs.md` | Framework trade-offs | plain SDK, LangChain, LangGraph, LlamaIndex, Pydantic AI, Haystack, DSPy; the four questions to judge them; how to find hidden prompts |

## Tasks (from the plan)
| Task | What |
|---|---|
| **1** (done) | A router: a small model classifies the user's intent into 4 to 5 categories and dispatches to specialised prompts; unclear intents go to the large model |
| **2** (done) | Use the Day 7 test set plus 30 new queries; measure router accuracy |
| **3** | Measure average cost and latency: router against always-large-model. Target: 40% cost reduction without quality loss. **Done:** 53.9% cheaper on a 14-query pilot, router slower (`Notes/task-3-router-cost-and-latency.md`) |
| **4** | A parallel "summarise 10 documents, then combine" chain with a concurrency limit; make one call fail and handle it |
| **5** | Rebuild the router flow in LangGraph (or Pydantic AI); compare lines of code, debuggability, latency and the hidden prompts the framework added |
| Notes | A framework comparison note |

## What Day 6 and 7 already give me
- **A classifier and its test sets:** `classify_query` v2 (30/30 on my hard set, about $0.000086 per call) and 60 labelled cases in `scripts/data/` (Day 7). The router will use 4 to 5 intents; the six Day 7 labels (admission, fees, schedule, academic, complaint, other) are the starting point.
- **The prompt registry:** `prompts/<name>/<version>.md`, loaded with `get_prompt`; each intent's specialised prompt becomes a registry file, and the name and version are logged with every call.
- **Cost and latency measuring:** the `llm_calls` table, `compute_cost()` and the evaluation script's accounting (tokens, cost, latency per call), which I can reuse for router against always-large.
- **Fan-out building blocks:** `LimitedClient` (calls in flight and per minute), `RetryingClient`, `FallbackClient`, and a fake provider that can fail on one chosen call.
- **A free-tier limit to plan for:** 15 calls per minute and 500 per day on the hosted model, and only 20 per day on the larger Gemini models, which decides how the "large model" for the router comparison is chosen.

## Two points to settle at the start of the build
- **Which models are "small" and "large"?** The hosted small model is `gemini-3.1-flash-lite`. A large model with enough free-tier requests per day has to be found, or the large side is simulated by a higher price table entry and a smaller test run; the cost target depends on this choice.
- **The router's test set:** the Day 7 sets have six labels and were written for a classifier, so the 30 new queries should include requests the router must send to the large model (unclear, two topics, long).
