# Day 9 task 1: load the corpus and split long documents by heading

Built: `day-9/scripts/load_corpus.py`. It reads `corpus/data/` (see `corpus/README.md`) and writes `documents.json`, `sections.json` and `skipped.json` next to it (git-ignored, because the text has its own licences; the script rebuilds them in about a minute). Environment: `day-9/pyproject.toml` with `numpy` and `pypdf`, installed with `uv sync`.

Run:
```
cd day-9
.venv\Scripts\python scripts\load_corpus.py
```

## 1. What the task asks
"Load 200+ corpus documents (split long ones by heading for now)."

- **Document:** one page or one chapter, the thing a person would call "a document".
- **Section:** a piece of a document, cut at a heading. One vector for a whole long document blurs its topics (learning note 2, section 6), so the sections are what will be embedded in task 2.

## 2. The result (real output of the last run)
```
234 documents, 2097 sections, 65 skipped

source                    docs  sections     words  median sec.  max sec.
fastapi-docs               135       840    103540           99       935
pydantic-docs               55       499     80720          100      1216
openstax-chemistry-2e       34       481    382861         1004      1471
arxiv-papers                10       277     95732          203      1436

section size in words: min 24, median 143, p95 1051, max 1471
sections over 1,000 words: 293 | under 60 words: 306
split methods: {'headings': 190, 'outline': 30, 'pages': 14}
sections cut into parts: 370
PDF outline entries placed by their title: 476 | placed at the page start (title not found): 22
```

| | |
|---|---|
| **Documents** | **234** (the task asks for 200+): 190 Markdown pages, 21 Chemistry chapters and 13 appendices, 10 papers |
| **Sections** | 2,097, about 663,000 words in all |
| **Licences** | MIT 190, CC BY-NC-SA 4.0 34, CC BY 4.0 9, CC0 1 (each document keeps its licence and attribution) |
| **Skipped** | 65: 58 stubs, 4 parts of the Chemistry book that are not content, 2 reference lists, 1 internal file |

## 3. The rules, and why
| Rule | Value | Why |
|---|---|---|
| A Markdown page at or under this size stays one section | 300 words | a short page is already one topic |
| A longer page is cut at headings of level 1 to 3 | not inside code fences | a `# comment` in a code block is not a heading |
| A section under this joins the next one | 40 words | a heading with two lines under it is a bad search result |
| A page under this is a stub and is skipped | 60 words | see section 4 |
| A PDF is cut at its own outline (bookmarks) | | the book and 8 of the 10 papers have one |
| A PDF without an outline is cut every 2 pages | | the 2 papers without bookmarks |
| A section over this is cut again at line breaks | 1,500 words, into parts of about 1,000 | see section 5 |

## 4. What the cleaning removed, and what it skipped
- **Markdown clean-up:** 452 code-include lines (FastAPI points to code samples in files outside `docs/`, so the text has the directive and not the code), 51 documentation directives (`::: pydantic.fields`), 8 front-matter blocks. The `/// note` and `!!! note` admonitions became "Note:" lines. The `{ #heading-id }` tags after FastAPI headings were removed.
- **1 internal file:** FastAPI's `_llm-test.md` is a test file for its translation tool, not documentation. I only noticed it in the trial embedding run (it was row 0). The loader now skips files whose name starts with an underscore, which changed the counts above from 235 documents and 2,109 sections.
- **58 stubs:** 36 Pydantic and 22 FastAPI pages with under 60 words after cleaning. Most Pydantic `api/` pages are only a directive, so after cleaning they are empty (0 words).
- **Chemistry:** Contents, Preface, Answer Key and Index are skipped. The 21 chapters and 13 appendices (periodic table, constants, thermodynamic tables) are kept.
- **Papers:** the References sections are dropped (931 and 17,281 words). One of them alone was bigger than most whole papers. References are noise for a question-answering corpus.

## 5. Things the measurement showed
- **PDF boundaries are mostly right, not exactly right.** 476 of 498 outline entries were found by their title in the extracted text (95.6%); 22 were placed at the start of their page. The first run found only 266: a paper's outline says "Introduction" while the page says "1 Introduction", and the fix was to allow a number in front.
  - Chemistry chapter 1 shows what is left: the "Chapter Outline" list sits in an "(opening)" section, and a running header ("1.1 • Chemistry in Context 11") can mark the start of a section instead of the real heading.
- **The sections are long.** The median is 141 words, but 293 are over 1,000 words, almost all from the textbook (its median is 1,004). With about 1.35 tokens per English word, 530 of the 2,097 sections are over 512 tokens. A model with a 512-token limit would silently cut the end of them.
  - **Parts:** without a limit the longest section was 17,297 words (a reference list) and the textbook sections reached 5,996. So a section over 1,500 words is cut into parts of about 1,000 words at line breaks (370 sections). After that the longest is 1,471 words, about 2,000 tokens, which fits even the smallest API limit (2,048). This is a stop-gap for task 2, not real chunking.
- **PDF text is raw.** pypdf gives lines in reading order of the file, not of the page: running headers and page numbers stay in, a table becomes a run of numbers, equations lose their layout, and a two-column paper can interleave its columns. The only repair I made is joining a word split by a hyphen at a line end ("re-" and "duced" become "reduced"). Parsing properly is Day 11; the search results of task 3 will show where it hurts.

## 6. What I did not do
- No quality check of the sections beyond samples and counts: no person has read them all.
- Markdown tables stay as text, and code blocks stay inside their sections. For a text embedding model a long code block is a lot of tokens with little meaning; that may show up in task 5.
- The order of documents is the order of files on disk (sorted), not a random sample, and the corpus is dominated by the textbook in word count (57%) although it is only 34 of 234 documents.

## Things that went wrong on the way
- **arXiv's certificate does not verify in Python on this machine** (`CERTIFICATE_VERIFY_FAILED`), while `curl` works. The download script calls `curl`, with certificate checking still on. Turning checking off was not an option.
- **A shell here-document changed the backslashes of my own Python text** (a `"\n"` became a real line break), which broke the script with a syntax error. I fixed the file with a direct edit, and I check a script with a syntax parse after every edit that contains backslashes.

## Quick check
- What is the difference between a document and a section in this corpus?
- Why are the References sections of the papers dropped?
- Why was a section over 1,500 words cut again, and why is that not the same as chunking?
- Why did the first run find only 266 of the 498 outline entries?
