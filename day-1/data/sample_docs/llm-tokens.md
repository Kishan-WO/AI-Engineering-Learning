# Tokens in Large Language Models

LLMs do not read characters or words. They read tokens, which are chunks of text produced by a tokenizer. In English, one token is roughly four characters.

Pricing, context window limits and latency are all measured in tokens. Languages other than English often need more tokens for the same meaning, which makes them more expensive to process.

Libraries such as tiktoken let you count tokens before sending a request.
