# Day 8 task 5: the router in plain code against LangGraph, and the framework comparison

Built: `ai-service/src/ai_service/services/router_graph.py` (the same router as a LangGraph graph), `tests/test_router_graph.py` (11 tests) and `scripts/run_router_framework_compare.py` (results in `scripts/results/router_framework_compare.json`). Decisions 61 to 63 are in `decisions.md`.

## 1. What I built
```
START -> rules --(intent found)-----------------+
              \--(no rule)--> classify ---------+--> answer_known --> END
                                                +--> answer_large --> END   (unclear)
```
- **State:** one `TypedDict` (`RouterState`) with the message, the intent, whether a rule matched, both answers' latencies and usage. A node returns only the keys it changes.
- **Nodes:** `rules`, `classify`, `answer_known`, `answer_large` (the two answer nodes share one helper). **Edges:** two conditional edges (after `rules`, after `classify`) that read `state["intent"]`.
- **The models are not LangChain objects.** Each node calls my own `LLMClient`, so retry, fallback, limits and cost logging stay exactly as they are, and the same prompt files and helpers (rules, label parser, `RouterResult`) are used by both flows. The graph is compiled once; the clients travel in as the run's context (`RouterDeps`).
- `route_with_graph(...)` has the same signature and result as `route()`. The API still uses the plain `route()`.

## 2. The comparison on my own code
| Measure | Plain `route()` | LangGraph |
|---|---|---|
| **Lines of code of the flow** (no blanks, comments or docstrings; shared helpers not counted) | 119 | 145 for the whole graph module (86 for the nodes, edges and compile) |
| **Same behaviour** | | 14 of 14 live queries gave the same intent; 7 offline cases gave the same result and the same requests |
| **Hidden prompts or extra calls** | none | **none**: for 14 live queries every request that left the process (the messages, `max_tokens`, feature, prompt name and version) was identical, with the same number of calls (14 of 14) |
| **The framework's own time per request** (a model that answers instantly) | 0.56 / 1.60 / 2.55 ms | 2.04 / 3.90 / 5.17 ms, so **+1.5 to +2.6 ms** (rule path / classify and known answer / classify and large answer) |
| **Latency with the real model** (14 queries, small model, alternating order) | median 5.06 s | median 5.15 s (**no measurable difference**, see 3) |
| **Debuggability when a call fails** | traceback of **2 frames**, all my code | **10 frames, 6 inside `langgraph`**; the exception is still my `LLMUnavailableError`, with a note added: `During task with name 'answer_known' and id ...` |
| **Dependencies added** | none | **20 new packages**, about **13.5 MB** on disk (`langgraph` and its checkpoint, prebuilt and sdk packages, `langchain-core`, `langsmith`, `orjson`, `requests`, `tenacity` and others) |
| **Import time of the router module** (cold process) | 0.56 s | 2.52 s |
| **Compiling the graph** | | 2.3 ms, once at import |

## 3. How to read the latency numbers
- The framework's cost is **about 2 ms per request** (measured against an instant model). A model call takes seconds, so this is below 0.1% of a request.
- The live medians (5.06 s against 5.15 s) differ by less than the noise: single queries differed by up to 30 seconds in either direction because the provider returned 503s and slow answers during the run. I do not read anything into the live difference. The measurement that isolates the framework is the offline one.

## 4. What the graph gives that the plain code does not
Checked in `tests/test_router_graph.py`:
- **Streaming steps:** `astream(..., stream_mode="updates")` yields one update per node: `rules`, `classify`, `answer_known`.
- **A drawing:** `get_graph().draw_mermaid()` gives a diagram of the flow.
- **Pause and resume:** with a checkpointer and `interrupt_before=["answer_large"]` the graph stops after classifying an unclear request, nothing has been sent to the large model, and the state is saved under a thread id. Calling it again with the same thread id continues and makes the large call. This is the "a person approves before the expensive call" case, and writing it in plain code would need my own state saving.

## 5. What it costs
- **More code for the same flow** (145 against 119 lines) and **a deeper traceback**. The flow is now spread over named nodes and edge functions, which is easy to draw and harder to read as one straight function.
- **20 new packages and a 4.5 times slower import.** The dependency list changes with every release; `uv.lock` pins it.
- **Lock-in is small here** because the nodes call my own client and my prompt registry. Leaving LangGraph means rewriting the wiring (about 86 lines), not the prompts, models or accounting.

## 6. What I did not test
- **LangChain's own model classes and prompt templates** (`ChatOpenAI`, `ChatPromptTemplate`, agents). Only `langgraph` and `langchain-core` are installed, and I did not use LangChain models, so hidden prompts that such classes can add (format instructions, tool descriptions) are not covered. "No hidden prompts" is true for **this** way of using LangGraph.
- **LangSmith tracing** comes with the install but is off unless an environment variable turns it on; I did not turn it on and did not test it.
- One flow, 14 queries, one run. The router is a small graph with no loop; the advantages of a graph grow with cycles and pauses, which this flow barely has.

## 7. My decision
Keep the plain `route()` for the API. The router is a straight flow with one branch, the framework adds nothing to it that I need today, and it costs 20 packages, a slower import and a deeper traceback. Use LangGraph when a flow needs a pause for a person, a loop, or resumable state; the pause-and-resume test shows that the router graph could do the "approve before the large model" step without a rewrite.

## Quick check
- Where did the extra 26 lines of the graph version go?
- Why is "no hidden prompts" true here, and for which way of using LangChain is it not tested?
- How do I see the exact request that leaves the process, and what did the comparison find?
- What does a checkpointer let me do that my plain function cannot?
