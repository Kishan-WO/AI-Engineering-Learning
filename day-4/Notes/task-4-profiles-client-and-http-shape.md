# Profiles, the client, and how I checked the HTTP shape

Questions: what is a profile and what do its parts do, how did we find out that the local and hosted APIs have the same HTTP shape, what is a client, and what does a result really look like (all its properties, not only the text)?

Tool: `day-4/tasks/task4_show_raw_response.py` sends the request by hand and prints everything. Run it any time:
```bash
uv run python tasks/task4_show_raw_response.py
uv run python tasks/task4_show_raw_response.py --profile local
```

## 1. What is a profile?
"Profile" is **my own name**, not a Python or API term. It is a small bundle of the settings needed to reach one provider, kept in one place:

```python
@dataclass(frozen=True)
class Profile:
    name: str                  # "local" or "gemini"
    base_url: str              # where the API lives
    api_key_env: str | None    # NAME of the environment variable that holds the key (None = no key)
    model_env: str             # NAME of the environment variable that holds the model name
    default_model: str         # used when the environment variable is empty
```
Real values (printed from the code):
```
PROFILES['local']  = Profile(name='local',  base_url='http://localhost:11434/v1', api_key_env=None,
                             model_env='LOCAL_MODEL', default_model='gemma3:270m')
PROFILES['gemini'] = Profile(name='gemini', base_url='https://generativelanguage.googleapis.com/v1beta/openai/',
                             api_key_env='GEMINI_API_KEY', model_env='GEMINI_MODEL', default_model='')
```
Note that a profile stores the **names** of the environment variables, not the secret itself. The key stays in `.env`.

### What `make_client(profile)` turns a profile into
```
make_client('local'):
   client.base_url = http://localhost:11434/v1/
   model           = gemma3:270m
   api key         = 'ollama'                       (any text; Ollama ignores it)
   type(client)    = openai.OpenAI

make_client('gemini'):
   client.base_url = https://generativelanguage.googleapis.com/v1beta/openai/
   model           = gemini-3.1-flash-lite          (from GEMINI_MODEL in .env)
   api key         = (a real key, 53 characters, hidden)
   type(client)    = openai.OpenAI
```
Same type of object, different settings. That is the whole trick: **the calling code never mentions a provider.**

### The parts
| Part | Role | Where its value comes from |
|---|---|---|
| `name` | The label used with `--profile` | The code |
| `base_url` | The address requests go to | The code (provider documentation) |
| `api_key_env` | Which environment variable holds the key | The code names it; `.env` holds the value |
| `model_env` | Which environment variable holds the model name | The code names it; `.env` holds the value |
| `default_model` | Fallback model | The code |

### Adding a provider
Add one entry to `PROFILES` (a base URL plus the two variable names) and put the values in `.env`. Nothing else changes.

## 2. What is a client?
A **client** is an object that knows how to talk to a server for me. It holds the connection settings (address, key, timeouts, retries) and has methods that:
1. build the HTTP request,
2. send it,
3. turn the JSON answer into Python objects.

JavaScript comparison: an `axios.create({ baseURL, headers })` instance, or the `OpenAI` object from the `openai` npm package.

These two do exactly the same thing:
```python
# with the client (what the code uses)
completion = client.chat.completions.create(model=model, messages=[...], temperature=0)

# by hand (what the client does for me): POST {base_url}/chat/completions with a JSON body
httpx.post(base_url + "/chat/completions", headers={"Authorization": "Bearer <key>"}, json={...})
```
The client also reuses connections, adds the `Authorization` header, retries some errors, and returns a typed `ChatCompletion` object instead of a raw dictionary.

## 3. How we know the two APIs have the same HTTP shape
"Same shape" means: the same URL path, the same request body fields, and the same response fields. I checked it in four ways:

1. **Documentation.** Ollama and Google both document an "OpenAI compatibility" mode, with the paths `/v1/chat/completions` (Ollama) and `/v1beta/openai/chat/completions` (Gemini). That tells me what to try, not that it works.
2. **The same request.** I sent the same JSON body to both addresses by hand with `httpx`, without the SDK. Both answered `200`.
3. **Comparing the responses.** `show_raw_response.py` lists every field name in each response and compares them (results below).
4. **The SDK parsed both.** The `openai` package turned both answers into the same class, `openai.types.chat.chat_completion.ChatCompletion`; it would have failed if the structure was different.

### Result of the comparison
Fields in **both** (14): `choices`, `choices[].finish_reason`, `choices[].index`, `choices[].message`, `choices[].message.content`, `choices[].message.role`, `created`, `id`, `model`, `object`, `usage`, `usage.completion_tokens`, `usage.prompt_tokens`, `usage.total_tokens`.

Only in Gemini: `choices[].message.extra_content.google.thought_signature`.
Only in Ollama: `system_fingerprint`, `usage.prompt_tokens_details.cached_tokens`.

So everything my code reads (`choices[0].message.content`, `finish_reason`, `usage.*`) exists in both. The differences are **extra optional fields** that my code ignores. That is what "compatible" really means: the common core is the same, and each provider adds its own extras.

How to check a new provider: add a profile and run `show_raw_response.py`; look at the "same shape" section at the end.

## 4. What the result really looks like
`reply.text` is only one piece. The full answer from the server is a JSON object.

### Request (identical for both, only `model` differs)
```
POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
Authorization: Bearer ***
Content-Type: application/json
{
  "model": "gemini-3.1-flash-lite",
  "messages": [ { "role": "user", "content": "Say hello in five words." } ],
  "temperature": 0,
  "max_tokens": 100
}
```

### Response from Gemini (status 200)
```json
{
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "message": {
        "content": "Hello, it is nice meeting.",
        "extra_content": { "google": { "thought_signature": "EnMKcQFpFH0TcN0THkpyXq... (a long opaque string)" } },
        "role": "assistant"
      }
    }
  ],
  "created": 1794477691,
  "id": "eo71atWhJozN694PnfLdqQs",
  "model": "gemini-3.1-flash-lite",
  "object": "chat.completion",
  "usage": { "completion_tokens": 7, "prompt_tokens": 7, "total_tokens": 14 }
}
```

### Response from the local Ollama model (status 200)
```json
{
  "id": "chatcmpl-967",
  "object": "chat.completion",
  "created": 1794477690,
  "model": "gemma3:270m",
  "system_fingerprint": "fp_ollama",
  "choices": [
    {
      "index": 0,
      "message": { "role": "assistant", "content": "Hello! " },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "prompt_tokens_details": { "cached_tokens": 0 },
    "completion_tokens": 4,
    "total_tokens": 19
  }
}
```

### Every property, explained
| Field | Meaning |
|---|---|
| `id` | Unique id of this response (useful in logs and bug reports) |
| `object` | Always `chat.completion` for a normal answer |
| `created` | Time the answer was made, as a Unix timestamp (seconds since 1970) |
| `model` | The model that answered |
| `system_fingerprint` | Ollama's label for the server setup (an OpenAI-style extra; not in Gemini's answer) |
| `choices` | A **list** of answers. Normally one; more only if `n` is set above 1 |
| `choices[].index` | Position of this answer in the list |
| `choices[].message.role` | Always `assistant` |
| `choices[].message.content` | **The text.** This is what my `Reply.text` holds |
| `choices[].message.extra_content` | Gemini-only extras, such as a thinking signature. I ignore it |
| `choices[].finish_reason` | Why the model stopped: `stop` (finished), `length` (hit `max_tokens`, text is cut), `tool_calls`, `content_filter` |
| `usage.prompt_tokens` | Tokens in my input (billed as input) |
| `usage.completion_tokens` | Tokens in the answer (billed as output; for thinking models this includes thinking tokens) |
| `usage.total_tokens` | The sum of the two |
| `usage.prompt_tokens_details.cached_tokens` | How many input tokens came from a cache (Ollama) |

### What the Python objects look like
```
type(completion) = openai.types.chat.chat_completion.ChatCompletion
completion.choices[0].message.content = 'Hello, it is nice meeting.'
completion.choices[0].finish_reason   = 'stop'
completion.usage = CompletionUsage(completion_tokens=7, prompt_tokens=7, total_tokens=14,
                                   completion_tokens_details=None, prompt_tokens_details=None)
```
and my own object, built from those:
```
Reply(text='Hello, it is nice meeting.', prompt_tokens=7, completion_tokens=7, seconds=0.73)
```
`Reply` keeps only what I need: the text, the two token counts and the time. Everything else is available on `completion` if I need it.

### Things I noticed in the real output
- The same prompt was **7 prompt tokens on Gemini and 15 on Ollama**. Different tokenisers, and Ollama also counts the chat template wrapped around the message.
- The local model's text is `'Hello! '` with a **trailing space**, so `.strip()` is useful (my `chat()` does it).
- The second Ollama call reported `cached_tokens=10`: it reused part of the prompt from the previous call.
- `finish_reason` was `stop` on both; if it had been `length`, the answer would have been cut.
- Gemini's answer ("Hello, it is nice meeting.") is five words; the small local model said only "Hello!". Quality and instruction-following differ even with the same request shape.

## Quick check
- What is stored in a `Profile`, and why does it store names of variables instead of the key?
- What does `make_client` return, and what is a client?
- How did I verify the two APIs share a shape, and what was different?
- Which field holds the answer text, and which one tells me the answer was cut?
- Why was the same prompt 7 tokens on one side and 15 on the other?
