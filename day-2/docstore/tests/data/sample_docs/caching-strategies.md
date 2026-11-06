# Caching Strategies

A cache stores the results of expensive work so they can be reused.

## Common patterns
- Cache-aside: the application checks the cache first and fills it on a miss.
- Time-to-live (TTL): entries expire after a fixed time.
- Prompt caching: LLM providers reuse a long, repeated prompt prefix at a lower cost.

The hardest part of caching is deciding when cached data is stale.
