# Embedding Batching and Rate Limits

In `scripts/embed_jina.py`, the embedding run batches sections before sending them to the provider API:

```python
BATCH_TEXTS = 32           # most texts in one request
BATCH_TOKENS = 12_000      # most estimated tokens in one request
TOKENS_PER_MINUTE = 90_000 # under Jina's 100,000 limit
REQUESTS_PER_MINUTE = 90   # under Jina's 100 limit
```

---

## 1. Rate Limit Constraints (Jina Free Tier)

* **Jina Free Tier Quota**: 100 Requests Per Minute (RPM) and 100,000 Tokens Per Minute (TPM).
* **Safety Margin**: `REQUESTS_PER_MINUTE = 90` and `TOKENS_PER_MINUTE = 90_000` provide a 10% safety buffer against slight timing drifts or estimation errors.

---

## 2. Why `BATCH_TOKENS = 12_000`?

1. **Smooth Pacing**:
   At ~12,000 tokens per batch, one batch represents ~13% of the minute's allowance ($12,000 / 90,000$). The rate pacer can dispatch one batch every 7–8 seconds smoothly, avoiding sharp bursts that trigger 429 errors.

2. **Mitigating HTTP Timeouts**:
   If a batch were 50,000+ tokens, the API server would spend 15–30+ seconds processing the embedding forward pass. This increases the likelihood of HTTP `504 Gateway Timeout` or socket read timeouts. At ~12,000 tokens, response latency remains predictable at **~1.5 to 2.5 seconds**.

3. **Blast Radius on Failure**:
   If a network glitch or 5xx error occurs, only 12,000 tokens need to be retried rather than an oversized payload.

---

## 3. Why `BATCH_TEXTS = 32`?

A token limit alone is insufficient because corpus sections vary widely in length:
* Many sections are brief (50–100 words), such as introductory notes, definitions, or short code explanations.
* Without an item ceiling, pack-by-token logic would bundle **100 to 200+ tiny sections** into a single JSON array. This causes excessive payload serialization overhead and risks exceeding API gateway payload size limits.
* **32** acts as an upper bound on count:
  - **Short sections**: Hitting `BATCH_TEXTS = 32` caps the request early, keeping JSON payloads lightweight.
  - **Long sections**: Hitting `BATCH_TOKENS = 12_000` caps the request first, naturally reducing the batch to 8–15 texts.

---

## 4. Dual-Ceiling Batching Rule

A batch closes as soon as **either** limit is reached:

$$\text{Next Batch} = \min(\text{count} \le 32,\; \text{estimated tokens} \le 12{,}000)$$

This dual ceiling ensures stable request sizes, minimal retry costs, and reliable adherence to provider rate limits.
