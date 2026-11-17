# Day 5: LLM integration I: Messages API, streaming and structured output

Build target: `POST /chat` (streaming) and a first `POST /extract` in `ai-service`.

The five tasks are one feature, so they were built directly into the `ai-service` project (`C:\Projects\ai-eng\ai-service`), not as separate scripts. This folder holds the learning notes and the evidence.

## Layout
```
day-5/
  README.md      this index
  learning/      the concept notes (written first)
  Notes/         what was built and the real results
```

## Learning notes (`learning/`)
| Note | Topic |
|---|---|
| `1.messages-api.md` | Roles, the message array (with the diagram), content blocks, stop reasons, Anthropic vs OpenAI shapes, sync and async SDKs |
| `2.streaming.md` | Why stream, provider events, SSE from FastAPI, saving the text, client disconnect, mid-stream errors |
| `3.structured-output.md` | Why free text breaks, JSON mode vs strict schema vs tool-as-schema, Pydantic, `instructor`, Literal, optional and "unknown" |

## Tasks (from the plan)
| Task | What | Status | Where |
|---|---|---|---|
| **1** | Tables `conversations` and `messages`, scoped by tenant | done | `ai-service/src/ai_service/db/models/conversation.py`, migration `c2b3d69c8756` |
| **2** | `POST /chat`: history, SSE streaming, save the assistant message | done | `api/v1/chat.py`, `services/chat_service.py`, `services/llm.py` |
| **3** | Stop the upstream stream when the client disconnects; verify in logs | done, verified live | `chat_stream()`; evidence in the Notes file, section 3 |
| **4** | `POST /extract`: messy text to a validated Pydantic model, native structured output | done | `api/v1/extract.py`, `services/extract_service.py` |
| **5** | The same `/extract` with a local model through Ollama; compare | done | `ai-service/scripts/compare_extract.py`; results in the Notes file, section 5 |
| Notes | The message-array diagram | done | `learning/1.messages-api.md`, section 3 |

Note with all outputs and results: `Notes/tasks-1-5-chat-and-extract.md`. Project-level notes: `ai-service/notes/day-5/01-chat-and-extract.md`, `decisions.md` (16 to 24), `gotchas.md`.

## Results in one line each
- `/chat` streams over SSE, remembers the conversation, and stores both messages with token counts.
- Closing the client mid-answer cancelled the stream, closed the upstream call and saved the partial text (`status = cancelled`), shown in the server log.
- `/extract` hosted: 10 of 10 valid, 98% of fields right, median 3.5 s. Local `gemma3:270m`: 9 of 10 valid, but only 39% of fields right, median 10.1 s.
- 73 tests, strict mypy and ruff pass.
