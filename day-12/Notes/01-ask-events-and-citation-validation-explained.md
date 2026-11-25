# `/ask` events and citation validation explained

Goes with `learning/3.citations.md`, sections 3 and 4. It shows what `/ask` sends over SSE and what the citation check does in code. The payloads are my sketch for the build, not a standard.

## 1. The events of one `/ask` request
| Event | When | Payload (JSON in `data:`) |
|---|---|---|
| `status` (optional) | a stage starts: `rewriting`, `retrieving`, `generating` | `{"stage": "retrieving"}` |
| `token` | for each piece of text from the LLM | `{"text": "Light travels "}` |
| `final` | once, after the last token | the verified answer and citations (below) |
| `error` | something failed, mid-stream or before | `{"code": "provider_unavailable", "message": "..."}` |

The `final` event:
```json
{
  "answer": "Light travels in straight lines [1].",
  "refused": false,
  "citations": [
    {"marker": 1, "chunk_id": "c_8f2a...", "document_id": "d_41", "title": "Light: Reflection", "page": 42, "excerpt": "..."}
  ],
  "invalid_markers": [],
  "usage": {"input_tokens": 1830, "output_tokens": 96, "cost_usd": 0.0}
}
```
- `refused` is true when the answer is the fixed refusal sentence (learning/2, section 3). A refusal has an empty `citations` list.
- `answer` is the **full** text (after any stripping) so a client can replace what it streamed.
- `usage` comes from the provider's last event (Day 5), and the same numbers go into the Day 6 request log.
- If the client disconnects, the upstream call is stopped (Day 5) and no `final` is sent.

## 2. The check, step by step
Given the numbered sources of this request: `{1: chunk_a, 2: chunk_b, 3: chunk_c}` and the full answer text.
1. **Find markers:** `[1]`, `[2][3]` and `[1, 3]` all appear in model output. The pattern must accept the three shapes. Test it on all of them.
2. **Collect the numbers:** a set of the integers found.
3. **Split:** valid = numbers in `{1, 2, 3}`; invalid = the rest.
4. **Act on invalid ones** (my decision to record): either remove `[7]` from the text, or leave the text and list `7` in `invalid_markers`.
5. **Build `citations`:** for each valid number, in order of first appearance, look up the chunk and copy the metadata.
6. **Refusal check:** if the answer equals the refusal sentence, set `refused` and ignore markers.
7. **Uncited answer check:** if the answer is not a refusal and has **no** marker, flag it (`no_citations: true`) and log it. A grounded answer without a citation is a prompt or model problem.

## 3. Cases to test (written before the code)
| Answer text | Sources given | Expected |
|---|---|---|
| `Light is a wave [1].` | 1 to 3 | valid `[1]`, citations = chunk 1 |
| `It reflects [2][3].` | 1 to 3 | valid 2 and 3, in this order |
| `It reflects [1, 3].` | 1 to 3 | valid 1 and 3 |
| `It is true [7].` | 1 to 3 | invalid 7, listed or stripped |
| `Light is a wave.` | 1 to 3 | flagged: no citation |
| `I couldn't find this in the material.` | 1 to 3 | refused, no citations |
| `[1]` inside a sentence quoting a source's own bracket | 1 to 3 | a real risk: a source can contain `[1]` as its own reference; I look at what happens |

The last row is why the check is a test case and not a one-line regex I trust.

## 4. What the check proves
- **Proved:** every marker in the output refers to a source I actually gave the model, and the user can open it.
- **Not proved:** the chunk says what the sentence claims; the answer has no uncited claims; the answer is correct. Task 4 (hand scoring) and Day 14 (judge) cover those.
- So `invalid_markers` is a **floor**: a zero there is necessary, not sufficient.

## 5. What to remember
- The stream carries text; the `final` event carries the truth.
- Test the marker pattern on every shape the model produces, and test the refusal.
- The model never sees chunk IDs; my code maps numbers to IDs, so the model cannot cite what I did not give it by inventing an ID.
