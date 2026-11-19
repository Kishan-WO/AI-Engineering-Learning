# Day 9 course corpus (used until Day 21)

The documents for the semantic search, RAG and agent work of Days 9 to 21. They are **not committed**
(`data/` is ignored): they have their own licences, and one file is 218 MB. What is committed is how to
get exactly the same files again: `manifest.json` (sources, pinned versions, licences) and
`download_corpus.py`.

## Sources
| Source | What | Licence | Pinned to |
|---|---|---|---|
| `fastapi-docs` | FastAPI documentation, English Markdown (`docs/en/docs/`, without `release-notes.md`) | MIT | `fastapi/fastapi` commit `05e6df7e90` |
| `pydantic-docs` | Pydantic documentation Markdown (`docs/`) | MIT | `pydantic/pydantic` commit `17873f3b65` |
| `openstax-chemistry-2e` | OpenStax *Chemistry 2e*, one PDF (tables, formulas, headings) | **CC BY-NC-SA 4.0** | `chemistry-2e_-_WEB.pdf` |
| `arxiv-papers` | ten research papers on embeddings, retrieval and RAG (two-column PDFs, equations, tables) | CC BY 4.0 (nine), CC0 (one), recorded **per paper** | arXiv ids in the manifest |

- **OpenStax licence:** the licence name was read from OpenStax's own CMS API (`license_name`,
  `license_version` of the book page). The book's preface page still says CC BY 4.0; the API says
  CC BY-NC-SA 4.0, so I use the stricter one: **noncommercial use only**, keep the attribution
  ("Chemistry 2e, OpenStax. Download for free at https://openstax.org/details/books/chemistry-2e"),
  and any adaptation carries the same licence. Fine for this learning project; not for a paid product.
- The MIT sources need the copyright notice kept; the manifest records it.

## Rebuild
```
python download_corpus.py           # the two Markdown sources, 249 files, about 1.5 MB
python download_corpus.py --pdf     # also the Chemistry PDF, about 218 MB
python download_corpus.py --papers  # also the ten arXiv papers, about 13 MB
```
`data/files.json` lists every file with its size and SHA-256.

## The papers
- Found with arXiv's search (embeddings, dense retrieval, RAG, Matryoshka, multilingual retrieval,
  reranking): 72 candidates. The licence of each one was read from arXiv's OAI metadata. Of the 72: 32 CC BY 4.0,
  2 CC0, 31 arXiv's own non-exclusive licence, and 7 CC BY-SA, CC BY-NC-SA or CC BY-NC-ND. Only **CC BY 4.0**
  and **CC0** were kept. Ten were chosen for their topic: Matryoshka embeddings, hybrid
  reranking, multilingual retrieval, chunk size in RAG, RAG surveys.
- Keep the attribution of each paper (title, authors, arXiv id) when quoting it; the manifest has it.
- The licence is the one the authors chose for the arXiv version. It does not cover figures taken from
  other works.
- arXiv's certificate chain does not verify in Python on this machine, so these downloads use `curl`
  (certificate checking stays on).

## What the first look showed
- 249 Markdown files: 158 FastAPI, 91 Pydantic. About 1,800 sections at heading levels 1 to 3.
- **56 files have under 60 words**: most are Pydantic `api/` pages (an auto-documentation
  directive only) and FastAPI index pages. They are not real documents and the loader will skip them,
  which leaves about 190 Markdown documents. The 200+ target is met with the Chemistry chapters
  (about 20 chapters split from the PDF) and by counting heading sections.
- FastAPI pages include their code samples with a directive that points to files outside `docs/`
  (`docs_src/`). The text here has the directive, not the code; the loader decides what to do with it.
