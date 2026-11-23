"""Day 9, task 1: load the corpus and split long documents by heading.

    .venv\\Scripts\\python scripts\\load_corpus.py

Reads corpus/data (see corpus/README.md) and writes two files next to it:
  data/documents.json   one entry per document (a Markdown page, a Chemistry chapter or appendix,
                        a paper): id, source, title, words, number of sections, licence, attribution
  data/sections.json    one entry per section: the text that will be embedded, with its heading path

A "document" is what a person would call one page or one chapter. A "section" is a piece of it cut at
a heading, because one vector for a whole long document blurs its topics (learning note 2, section 6).

Rules (kept simple on purpose; smarter chunking is Day 11 and 12):
  Markdown   cut at headings of level 1 to 3 (not inside code fences) when the page has more than
             SPLIT_ABOVE words; a section under MIN_SECTION words joins the next one.
  PDF        cut at the entries of the PDF's own outline (its bookmarks); when a PDF has none, cut
             every PAGES_PER_SECTION pages. The page text is what pypdf extracts: columns, running
             headers and table layout are NOT repaired (that is Day 11).
  Long       a section over MAX_SECTION_WORDS words is cut again at line breaks into parts of about
             PART_WORDS words, so a model with a short input limit does not silently drop the end of
             it (a stop-gap; real chunking is Day 11).
  Skipped    a page under MIN_DOCUMENT_WORDS words after cleaning (stubs), PDF parts that are not
             content (Contents, Preface, Answer Key, Index) and the References section of a paper.
             Every skip is listed in the output.
"""

import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
DATA = CORPUS / "data"

SPLIT_ABOVE = 300  # words: a Markdown page at or under this stays one section
MIN_SECTION = 40  # words: a smaller section is joined to the next one
MIN_DOCUMENT_WORDS = 60  # words: a page under this is a stub and is skipped
PAGES_PER_SECTION = 2  # for a PDF without an outline
MAX_SECTION_WORDS = 1500  # a longer section is cut into parts
PART_WORDS = 1000  # the size a part aims for
REFERENCES = re.compile(r"^\d*\.?\s*(references|bibliography)\s*$", re.I)
HEADING_ID = re.compile(r"\s*\{\s*#[\w-]+\s*\}\s*$")  # FastAPI: ## Title { #title }
NEWLINE = "\n"
PDF_MATCH: Counter = Counter()  # outline entries found by their title / placed by page
SKIP_PDF_PARTS = re.compile(r"^(contents|preface|answer key|index)$", re.I)

FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^(#{1,3})\s+(.+?)\s*#*\s*$")
INCLUDE = re.compile(r"^\s*(\{\*.*\*\}|\{!.*!\}|--8<--.*)\s*$")  # code-sample includes
DIRECTIVE = re.compile(r"^\s*:::\s*\S+")  # mkdocstrings: ::: pydantic.fields
SLASH_ADMONITION = re.compile(r"^\s*///\s*(\w+)?\s*(?:\|\s*(.*))?$")  # FastAPI: /// note | Title
BANG_ADMONITION = re.compile(r'^\s*!!!\s*(\w+)\s*(?:"(.*)")?\s*$')  # Pydantic: !!! note "Title"
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "section"


def words(text: str) -> int:
    return len(text.split())


# ---------------------------------------------------------------- Markdown


def clean_markdown(raw: str) -> tuple[str, Counter]:
    """Remove what is not prose (front matter, code-sample includes, directives, comments)."""
    removed: Counter = Counter()
    text = HTML_COMMENT.sub("", raw.replace("\r\n", "\n"))
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            text, removed["front_matter"] = text[end + 5 :], 1
    out: list[str] = []
    in_fence = False
    dedent_after_bang = False
    for line in text.split("\n"):
        if FENCE.match(line):
            in_fence = not in_fence
        if not in_fence:
            if INCLUDE.match(line):
                removed["code_include"] += 1
                continue
            if DIRECTIVE.match(line):
                removed["directive"] += 1
                continue
            m = BANG_ADMONITION.match(line)
            if m:
                out.append(f"{m.group(1).capitalize()}: {m.group(2)}" if m.group(2) else f"{m.group(1).capitalize()}:")
                dedent_after_bang = True
                continue
            if dedent_after_bang:
                if line.startswith("    "):
                    line = line[4:]
                elif line.strip():
                    dedent_after_bang = False
            m = SLASH_ADMONITION.match(line)
            if m and line.strip().startswith("///"):
                kind, title = m.group(1), m.group(2)
                if kind:  # an opening line; the closing "///" has no kind and is dropped
                    out.append(f"{kind.capitalize()}: {title}" if title else f"{kind.capitalize()}:")
                continue
        if re.match(r"^#{1,6}\s", line) and not in_fence:  # any heading level, not only 1 to 3
            line = HEADING_ID.sub("", line)
        out.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip(), removed


def split_markdown(text: str, title: str) -> list[dict]:
    """Sections cut at headings of level 1 to 3, outside code fences."""
    if words(text) <= SPLIT_ABOVE:
        return [{"heading_path": [title], "text": text}]
    pieces: list[dict] = []
    path: list[tuple[int, str]] = []
    current: list[str] = []
    heading_path = [title]
    in_fence = False

    def flush() -> None:
        body = "\n".join(current).strip()
        if body:
            pieces.append({"heading_path": list(heading_path), "text": body})

    for line in text.split("\n"):
        if FENCE.match(line):
            in_fence = not in_fence
        m = None if in_fence else HEADING.match(line)
        if m:
            flush()
            current = []
            level, name = len(m.group(1)), m.group(2).strip()
            while path and path[-1][0] >= level:
                path.pop()
            path.append((level, name))
            heading_path = [n for _, n in path]
        current.append(line)
    flush()
    return join_small(pieces)


def join_small(pieces: list[dict]) -> list[dict]:
    """A section under MIN_SECTION words is joined to the next one (the last one, to the previous)."""
    merged: list[dict] = []
    carry: dict | None = None
    for piece in pieces:
        if carry is not None:
            piece = {"heading_path": carry["heading_path"], "text": carry["text"] + "\n\n" + piece["text"]}
            carry = None
        if words(piece["text"]) < MIN_SECTION:
            carry = piece
        else:
            merged.append(piece)
    if carry is not None:
        if merged:
            merged[-1]["text"] += "\n\n" + carry["text"]
        else:
            merged.append(carry)
    return merged


def cap_size(pieces: list[dict]) -> list[dict]:
    """Cut a section over MAX_SECTION_WORDS into parts of about PART_WORDS words, at line breaks."""
    out: list[dict] = []
    for piece in pieces:
        if words(piece["text"]) <= MAX_SECTION_WORDS:
            out.append(piece)
            continue
        parts: list[str] = []
        current: list[str] = []
        count = 0
        for line in piece["text"].splitlines():
            current.append(line)
            count += len(line.split())
            if count >= PART_WORDS and (line.rstrip().endswith((".", ":", "?", "!")) or count >= PART_WORDS * 1.3):
                parts.append(NEWLINE.join(current).strip())
                current, count = [], 0
        rest = NEWLINE.join(current).strip()
        if rest:
            if parts and count < MIN_SECTION:
                parts[-1] += NEWLINE + rest
            else:
                parts.append(rest)
        for i, body in enumerate(parts, start=1):
            out.append({"heading_path": piece["heading_path"] + [f"part {i} of {len(parts)}"], "text": body})
    return out


# ---------------------------------------------------------------- PDF


def outline_entries(reader: PdfReader) -> list[tuple[int, str, int]]:
    """(depth, title, first page as 1-based number) for every outline entry that has a page."""
    entries: list[tuple[int, str, int]] = []

    def walk(items, depth: int = 0) -> None:
        for item in items:
            if isinstance(item, list):
                walk(item, depth + 1)
                continue
            try:
                entries.append((depth, str(item.title).strip(), reader.get_destination_page_number(item) + 1))
            except Exception:  # an outline entry with a broken destination
                continue

    try:
        walk(reader.outline)
    except Exception:
        return []
    return entries


def page_text(reader: PdfReader, number: int) -> str:
    text = reader.pages[number - 1].extract_text() or ""
    text = text.replace("\x00", "").replace("­", "")
    text = re.sub(r"(?<=[a-z])-\n(?=[a-z])", "", text)  # "re-" at a line end, "duced" on the next
    return re.sub(r"[ \t]+\n", "\n", text)


def title_pattern(title: str) -> re.Pattern:
    parts = [re.escape(p) for p in re.findall(r"\w+", title)]
    # a paper's outline says "Introduction" while the page says "1 Introduction": allow a number first
    number = r"(?:[A-Z]|\d+)(?:\.\d+)*\.?\s+"
    return re.compile(r"(?mi)^\s*(?:" + number + r")?" + r"\W+".join(parts)) if parts else re.compile(r"(?!x)x")


def split_pdf_range(reader: PdfReader, first: int, last: int, entries: list[tuple[int, str, int]], doc_title: str) -> tuple[list[dict], str]:
    """Sections of pages first..last, cut at the given outline entries (or by pages when none)."""
    page_starts: list[int] = []
    chunks: list[str] = []
    total = 0
    for n in range(first, last + 1):
        page_starts.append(total)
        t = page_text(reader, n)
        chunks.append(t)
        total += len(t) + 1
    text = "\n".join(chunks)

    if not entries:
        sections = []
        for i in range(first, last + 1, PAGES_PER_SECTION):
            j = min(i + PAGES_PER_SECTION - 1, last)
            body = "\n".join(chunks[i - first : j - first + 1]).strip()
            if body:
                sections.append({"heading_path": [doc_title, f"pages {i}-{j}"], "text": body, "pages": [i, j]})
        return join_small(sections), "pages"

    starts: list[tuple[int, str, int]] = []
    pos = 0
    for depth, title, page in entries:
        page_offset = page_starts[min(max(page, first), last) - first]
        m = title_pattern(title).search(text, max(pos, page_offset))
        found = bool(m and m.start() < page_offset + 20000)
        PDF_MATCH["found" if found else "page start"] += 1
        start = m.start() if found else max(pos, page_offset)
        pos = max(pos, start)
        starts.append((pos, title, depth))
    sections = []
    # text before the first entry belongs to the document's opening
    if starts and starts[0][0] > 0 and text[: starts[0][0]].strip():
        sections.append({"heading_path": [doc_title, "(opening)"], "text": text[: starts[0][0]].strip()})
    stack: list[tuple[int, str]] = []
    for i, (start, title, depth) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        body = text[start:end].strip()
        while stack and stack[-1][0] >= depth:
            stack.pop()
        stack.append((depth, title))
        if body:
            sections.append({"heading_path": [doc_title] + [t for _, t in stack], "text": body})
    return join_small(sections), "outline"


# ---------------------------------------------------------------- main


def load() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))
    sources = {s["id"]: s for s in manifest["sources"]}
    documents: list[dict] = []
    sections: list[dict] = []
    skipped: list[dict] = []

    def add(doc: dict, pieces: list[dict], method: str) -> None:
        pieces = cap_size(pieces)
        doc["sections"] = len(pieces)
        doc["split_method"] = method
        doc["words"] = sum(words(p["text"]) for p in pieces)
        documents.append(doc)
        for i, p in enumerate(pieces, start=1):
            sections.append(
                {
                    "id": f"{doc['id']}#{i:03d}-{slug(p['heading_path'][-1])}",
                    "doc_id": doc["id"],
                    "source": doc["source"],
                    "title": doc["title"],
                    "heading_path": p["heading_path"],
                    "text": p["text"],
                    "words": words(p["text"]),
                    "licence": doc["licence"],
                }
            )

    # ---- Markdown
    for sid in ("fastapi-docs", "pydantic-docs"):
        src = sources[sid]
        for path in sorted((DATA / sid).rglob("*.md")):
            rel = path.relative_to(DATA / sid).as_posix()
            if path.name.startswith("_"):  # e.g. FastAPI's _llm-test.md, a test file for its translation tool
                skipped.append({"doc": f"{sid}/{rel}", "reason": "internal file (the name starts with an underscore), not documentation"})
                continue
            text, removed = clean_markdown(path.read_text(encoding="utf-8"))
            first_h1 = next((HEADING.match(l).group(2) for l in text.split("\n") if HEADING.match(l) and l.startswith("# ")), None)
            title = first_h1 or rel.removesuffix(".md").replace("-", " ").replace("_", " ").title()
            if words(text) < MIN_DOCUMENT_WORDS:
                skipped.append({"doc": f"{sid}/{rel}", "reason": f"stub: {words(text)} words after cleaning", "removed": dict(removed)})
                continue
            doc = {"id": f"{sid}/{rel}", "source": sid, "kind": "markdown", "title": title, "licence": src["licence"], "attribution": src["attribution"], "removed_lines": dict(removed)}
            add(doc, split_markdown(text, title), "headings")

    # ---- OpenStax Chemistry: one document per chapter and per appendix
    src = sources["openstax-chemistry-2e"]
    pdf = next((DATA / "openstax-chemistry-2e").glob("*.pdf"))
    reader = PdfReader(str(pdf))
    entries = outline_entries(reader)
    top = [(i, t, p) for i, (d, t, p) in enumerate(entries) if d == 0]
    for k, (idx, title, first) in enumerate(top):
        nxt = top[k + 1][0] if k + 1 < len(top) else len(entries)
        last = (top[k + 1][2] - 1) if k + 1 < len(top) else len(reader.pages)
        if SKIP_PDF_PARTS.match(title):
            skipped.append({"doc": f"openstax-chemistry-2e/{title}", "reason": "not content (front or back matter)"})
            continue
        sub = [e for e in entries[idx + 1 : nxt] if e[0] >= 1]
        pieces, method = split_pdf_range(reader, first, last, sub, title)
        doc = {"id": f"openstax-chemistry-2e/{slug(title)}", "source": "openstax-chemistry-2e", "kind": "pdf", "title": title, "pages": [first, last], "licence": src["licence"], "attribution": src["attribution"]}
        add(doc, pieces, method)

    # ---- arXiv papers: one document per paper
    src = sources["arxiv-papers"]
    for paper in src["papers"]:
        reader = PdfReader(str(DATA / "arxiv-papers" / f"{paper['arxiv_id']}.pdf"))
        entries = outline_entries(reader)
        pieces, method = split_pdf_range(reader, 1, len(reader.pages), entries if len(entries) >= 3 else [], paper["title"])
        dropped = [p for p in pieces if REFERENCES.match(p["heading_path"][-1])]
        pieces = [p for p in pieces if p not in dropped]
        for p in dropped:
            skipped.append({"doc": f"arxiv-papers/{paper['arxiv_id']}", "reason": f"References section dropped ({words(p['text'])} words)"})
        if sum(words(p["text"]) for p in pieces) < MIN_DOCUMENT_WORDS:
            skipped.append({"doc": f"arxiv-papers/{paper['arxiv_id']}", "reason": "no extractable text"})
            continue
        doc = {"id": f"arxiv-papers/{paper['arxiv_id']}", "source": "arxiv-papers", "kind": "pdf", "title": paper["title"], "pages": [1, len(reader.pages)], "licence": paper["licence"], "attribution": paper["attribution"]}
        add(doc, pieces, method)

    (DATA / "documents.json").write_text(json.dumps(documents, indent=1, ensure_ascii=False), encoding="utf-8")
    (DATA / "sections.json").write_text(json.dumps(sections, indent=1, ensure_ascii=False), encoding="utf-8")
    (DATA / "skipped.json").write_text(json.dumps(skipped, indent=1, ensure_ascii=False), encoding="utf-8")
    report(documents, sections, skipped)


def report(documents: list[dict], sections: list[dict], skipped: list[dict]) -> None:
    print(f"\n{len(documents)} documents, {len(sections)} sections, {len(skipped)} skipped\n")
    print(f"{'source':<24}{'docs':>6}{'sections':>10}{'words':>10}{'median sec.':>13}{'max sec.':>10}")
    for sid in dict.fromkeys(d["source"] for d in documents):
        ds = [d for d in documents if d["source"] == sid]
        ss = sorted(s["words"] for s in sections if s["source"] == sid)
        print(f"{sid:<24}{len(ds):>6}{len(ss):>10}{sum(d['words'] for d in ds):>10}{ss[len(ss) // 2]:>13}{ss[-1]:>10}")
    all_w = sorted(s["words"] for s in sections)
    print(f"\nsection size in words: min {all_w[0]}, median {all_w[len(all_w) // 2]}, p95 {all_w[int(len(all_w) * .95)]}, max {all_w[-1]}")
    print("sections over 1,000 words:", sum(w > 1000 for w in all_w), "| under 60 words:", sum(w < 60 for w in all_w))
    print("split methods:", dict(Counter(d["split_method"] for d in documents)))
    print("sections cut into parts:", sum(1 for s in sections if s["heading_path"][-1].startswith("part ")))
    print("PDF outline entries placed by their title:", PDF_MATCH["found"], "| placed at the page start (title not found):", PDF_MATCH["page start"])
    print("\nskipped:")
    for s in skipped:
        print("  ", s["doc"], "-", s["reason"])


if __name__ == "__main__":
    load()
