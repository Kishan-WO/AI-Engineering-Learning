# Chunk Sizing and Long Section Splitting

In `scripts/load_corpus.py`, the corpus loader splits Markdown and PDF documents by headings and outline entries. However, some sections can be several thousand words long (e.g. comprehensive tutorials, multi-topic API reference pages, or long paper sections).

To prevent oversized chunks from entering the embedding index, the loader configures:

```python
MAX_SECTION_WORDS = 1500  # a longer section is cut into parts
PART_WORDS = 1000         # the size a part aims for
```

---

## 1. Why Long Sections Cannot Stay Intact

1. **Embedding Dilution**:
   An embedding model condenses the semantic meaning of an entire chunk into a single fixed-length vector (e.g., 1024 dimensions in Jina or BGE-M3). When a section spans 2,500 words across diverse topics, the vector becomes an average of everything mentioned, diluting specific concepts and causing queries for specific sub-details to score poorly.

2. **Context Window and Token Waste**:
   Injecting a 2,000-word chunk into an LLM context during RAG consumes ~2,800 tokens. If `top_k = 5`, that single document could monopolise the prompt token budget.

3. **Model Context Limits**:
   While modern models (like Jina v3 and BGE-M3) support 8,192 tokens, many embedding models (e.g., `text-embedding-3-small` or standard open-source bi-encoders) have tighter input ceilings (512 to 2,048 tokens).

---

## 2. The Splitting Logic (`split_long_sections`)

When a section exceeds `MAX_SECTION_WORDS = 1500`, it is sliced using `PART_WORDS = 1000` as the target size:

```python
for line in piece["text"].splitlines():
    current.append(line)
    count += len(line.split())
    if count >= PART_WORDS and (line.rstrip().endswith((".", ":", "?", "!")) or count >= PART_WORDS * 1.3):
        parts.append(NEWLINE.join(current).strip())
        current, count = [], 0
```

### Key Mechanisms:
- **Target Size (`PART_WORDS = 1000`)**: Aims for slices of roughly 1,000 words (~1,300–1,400 tokens), which is a sweet spot for maintaining paragraph context while remaining semantically focused.
- **Natural Boundary Detection**: It does not blindly cut at the 1,000th word. It waits for punctuation indicating the end of a sentence or bullet point (`.`, `:`, `?`, `!`).
- **Flexibility Window (`PART_WORDS * 1.3 = 1300`)**: If a section has unusually long prose or code blocks without sentence-ending punctuation, it will not run away indefinitely; it hard-cuts at 1,300 words.
- **Orphan Prevention (`MIN_SECTION = 40`)**: Any leftover trailing text shorter than 40 words is merged into the previous part rather than forming an isolated fragment.
- **Heading Path Continuity**: Slices receive explicit provenance in their metadata, e.g. `["FastAPI", "Security", "part 1 of 3"]`.
