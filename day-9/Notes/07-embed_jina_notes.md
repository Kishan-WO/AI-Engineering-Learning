# Notes on `embed_jina.py`

Contents:

1. The main loop (lines 159-203)
2. How the `Pacer` works
3. `.npy` and `.json` files

---

# 1. The main loop (lines 159-203)

This is the main loop of `main()`. It sends the sections to Jina in batches, saves each batch as it returns, and then combines everything into one final file.

## 1.1 Setup (159-163)

```python
pacer = Pacer()
started = time.time()
stats = {...}
batch_log = []
parts = []
```

- `pacer` is the rate limiter. It makes sure you stay under 90 requests and 90,000 tokens per minute.
- `started` is the start time, used for the total-time report at the end.
- `stats` holds running counters for tokens, retries, waiting time and so on.
- `batch_log` keeps one small log entry per batch.
- `parts` collects the vector arrays of each batch, in order.

## 1.2 Resume from disk (164-175)

```python
for n, idx in enumerate(batches):
    ids = [sections[i]["id"] for i in idx]
    npy, js = ... batch_0000.npy, batch_0000.json
    if npy.exists() and js.exists():
        saved = json.loads(...)
        if saved["ids"] == ids and saved["hashes"] == [hashes[i] for i in idx]:
            parts.append(np.load(npy))
            ...
            continue
```

The loop goes through every batch (`idx` is the list of section indexes in that batch). Before calling the API, it checks whether this batch was already saved by an earlier run.

It only reuses the saved file if both the **section IDs** and the **text hashes** match. So if you changed the text of a section since the last run, the hash differs and the batch is re-embedded instead of using stale vectors. When a batch is reused, `continue` skips the API call. This is why a run that crashed can simply be started again.

## 1.3 Call the API (176-182)

```python
est = sum(estimate_tokens(texts[i]) for i in idx)
waited = pacer.wait_for(est)
event = pacer.record(est)
t0 = time.perf_counter()
vectors, tokens, retries = request_batch(key, [texts[i] for i in idx])
elapsed = time.perf_counter() - t0
event[1] = tokens
```

1. Estimate the tokens of this batch.
2. `pacer.wait_for(est)` sleeps if sending now would exceed the per-minute budget.
3. `pacer.record(est)` registers the request in the pacer's 60-second window, using the estimate for now.
4. `request_batch` makes the real HTTP call (with its own retry logic) and returns the vectors, Jina's real token count, and the number of retries.
5. `event[1] = tokens` replaces the estimate with the real token count, so the pacer's budget stays accurate.

## 1.4 Save immediately (183-188)

```python
arr = np.array(vectors, dtype=np.float32)
np.save(npy, arr)
log = {...}
js.write_text(json.dumps({...}))
parts.append(arr)
batch_log.append(log)
```

The vectors are converted to a float32 array and written to disk **right away**, together with a JSON file holding the IDs, hashes and token count. That JSON is what the resume check in 1.2 reads. The array and log are also kept in memory for the final assembly.

## 1.5 Update statistics and print progress (189-194)

These lines add this batch's tokens, retries, waiting time and API time to `stats`. The `print` shows progress like `batch 3/20: 32 texts, 8,500 tokens (estimated 9,100), 1.2s, waited 0s | total ...`. Comparing the real and estimated token counts shows how good the estimator is.

## 1.6 Combine and validate (196-203)

```python
vectors = np.concatenate(parts).astype(np.float32)
norms = np.linalg.norm(vectors, axis=1)
if vectors.shape != (len(sections), DIMENSIONS):
    sys.exit(...)
if not np.all(np.isfinite(vectors)):
    sys.exit(...)
normalised = bool(np.allclose(norms, 1.0, atol=1e-3))
np.save(out / "vectors.npy", vectors)
```

After the loop:

- `np.concatenate(parts)` stacks all batch arrays into one matrix with one row per section, in the original order.
- `norms` is the length of each vector.
- **Shape check:** the matrix must be exactly `(number of sections, 1024)`, otherwise the script stops.
- **Sanity check:** the script stops if any value is NaN or infinity.
- `normalised` records whether Jina already returned unit-length vectors (norm ≈ 1). This matters later: if they are normalised, a dot product equals cosine similarity.
- Finally, the whole matrix is saved as `vectors.npy`.

## 1.7 The design idea

The script is built to survive failure. Each batch is saved as it arrives, and a restart reuses what is valid and redoes only what is missing or changed. The final checks make sure the output is complete before the "official" file is written.

---

# 2. How the `Pacer` works

The pacer is a **sliding 60-second window**. It remembers every request sent in the last minute, and before sending a new one it checks: "if I send this now, will I go over the limit?" If yes, it sleeps until old requests fall out of the window.

## 2.1 What it stores

```python
self.events = deque()   # each item: [time_sent, tokens]
```

Example after 3 requests:

```
[ [10.0, 8000], [12.5, 9000], [15.0, 7000] ]
```

Each entry says "at time 10.0 seconds, I sent a request that used 8000 tokens."

## 2.2 `wait_for(tokens)`: the check

```python
while True:
    now = time.monotonic()
    # 1. forget requests older than 60 seconds
    while self.events and now - self.events[0][0] >= 60:
        self.events.popleft()
    # 2. count what is still inside the window
    used = sum(e[1] for e in self.events)
    # 3. is there room?
    if used + tokens <= TOKENS_PER_MINUTE and len(self.events) < REQUESTS_PER_MINUTE:
        return waited
    # 4. no room: sleep until the oldest request leaves the window
    pause = max(60 - (now - self.events[0][0]), 0.5) if self.events else 1.0
    time.sleep(pause)
    waited += pause
```

Step by step:

1. **Drop old events.** Anything sent 60+ seconds ago no longer counts against the limit. Because events are in time order, only the left side (oldest) needs checking.
2. **Add up tokens** of the remaining events.
3. **Two conditions must both hold** to proceed: tokens used plus the new batch must be at most 90,000, and fewer than 90 requests in the window. If so, it returns immediately.
4. **Otherwise it sleeps** just long enough for the oldest event to expire (`60 - age of oldest`), then loops and checks again. The minimum of 0.5 seconds avoids a busy loop.

It returns `waited`, the total seconds it slept (used only for statistics).

## 2.3 `record(tokens)`: write it down

```python
event = [time.monotonic(), tokens]
self.events.append(event)
return event
```

This adds the new request to the window, stamped with the current time, and returns that same list object.

## 2.4 Why two calls, and why `event[1] = tokens` later

```python
waited = pacer.wait_for(est)    # 1. may sleep, then returns when it is safe
event = pacer.record(est)       # 2. register the request (estimated tokens)
... request_batch(...) ...      # 3. real API call
event[1] = tokens               # 4. fix the entry with the real token count
```

Before the call, the script only has an **estimate** of the tokens, so it records the estimate. After the call, Jina reports the **real** count. Because `record` returned the very same list stored in the deque, `event[1] = tokens` edits that entry in place. The pacer's history is now accurate without searching for the entry.

## 2.5 A concrete example

Say the limit were 20,000 tokens per minute, and the window holds:

```
[ [0s, 9000], [5s, 9000] ]     -> used = 18,000
```

A new batch of 5,000 tokens arrives at 10s. `18,000 + 5,000 > 20,000`, so it must wait. The oldest event is 10s old, so it sleeps `60 - 10 = 50s`. At 60s, the first event is dropped, `used = 9,000`, and `9,000 + 5,000 <= 20,000`, so it proceeds.

The script uses 90,000 instead of Jina's real limit of 100,000 as a safety margin, because token counts are estimated and the clock on Jina's side may not match exactly.

---

# 3. `.npy` and `.json` files

Both are just file formats for saving data. The script uses each for what it's good at: **`.npy` for the numbers, `.json` for the descriptive information.**

## 3.1 `.npy`: a saved NumPy array

An `.npy` file is NumPy's own binary format for storing an array exactly as it exists in memory.

```python
arr = np.array(vectors, dtype=np.float32)
np.save(npy, arr)        # write to disk
arr = np.load(npy)       # read back, identical array
```

In this script, each batch's `.npy` holds a matrix like this:

```
shape (32, 1024)  ->  32 rows (one per section), 1024 numbers per row
```

Why not store the vectors in JSON instead?

- **Size:** JSON writes every number as text (`0.0123456789`), which takes far more space. A float32 in `.npy` is exactly 4 bytes.
- **Speed:** loading `.npy` is almost instant, while parsing JSON text is slow for large arrays.
- **Precision:** the exact float32 values are preserved, with no text conversion.
- **Not human-readable:** you can't open it in a text editor. That's the trade-off.

## 3.2 `.json`: a readable text file

JSON stores structured data (dicts, lists, strings, numbers) as plain text you can open and read.

```python
js.write_text(json.dumps({"ids": ids, "hashes": [...], "tokens": tokens, "log": log}))
saved = json.loads(js.read_text())
```

A batch's JSON file looks something like:

```json
{
  "ids": ["doc1-s0", "doc1-s1", "doc2-s0"],
  "hashes": ["a3f9...", "9c1d...", "77be..."],
  "tokens": 8500,
  "log": {"batch": 0, "texts": 3, "tokens": 8500, "seconds": 1.2, "retries": 0}
}
```

It holds information **about** the batch, not the vectors themselves: which sections it contains, the hash of each text, how many tokens it used.

## 3.3 Why each batch gets both files

```
batches/
  batch_0000.npy    <- the vectors (the heavy data)
  batch_0000.json   <- who they belong to + proof they are still valid
```

They work as a pair. The resume check at the start of the loop needs both:

```python
if npy.exists() and js.exists():
    saved = json.loads(js.read_text())
    if saved["ids"] == ids and saved["hashes"] == [...]:
        parts.append(np.load(npy))
```

The JSON answers: "is this saved batch still correct for the current texts?" (IDs and hashes match). If yes, the `.npy` supplies the vectors without calling the API again.

Requiring both files to exist also gives a little safety. The script writes `.npy` first and `.json` second, so if it crashed in between, the JSON would be missing and the batch would simply be redone rather than trusted.

## 3.4 The final outputs follow the same split

- `vectors.npy`: all vectors combined, shape `(number of sections, 1024)`
- `meta.json`: the model settings, per-row info (id, title, hash) and run statistics

Row `i` of `vectors.npy` corresponds to entry `i` in `meta.json`, which is how you later find out which section a vector came from.
