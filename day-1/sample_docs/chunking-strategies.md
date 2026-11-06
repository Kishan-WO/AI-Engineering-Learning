# Chunking Strategies

Before documents can be embedded, they are split into chunks.

Fixed-size chunking splits text every N tokens or words, usually with some overlap so that sentences on a boundary are not lost. Recursive chunking splits on paragraphs, then sentences, then words. Structure-aware chunking follows headings and keeps tables together.

Chunks that are too small lose context; chunks that are too large dilute the meaning and waste tokens.
