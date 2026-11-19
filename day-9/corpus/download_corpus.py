"""Download the Day 9 corpus described in manifest.json into data/ (standard library only).

    python download_corpus.py            # the two Markdown sources (about 2 MB)
    python download_corpus.py --pdf      # also the OpenStax Chemistry 2e PDF (about 218 MB)
    python download_corpus.py --papers   # also the ten arXiv papers (about 13 MB)

- The Markdown files come from GitHub at a PINNED commit (see the manifest), so every run gets the
  same text. The list of files comes from the GitHub tree API; every path is checked before it is
  used (inside the expected folder, ends in .md, no "..").
- Every downloaded file is recorded in data/files.json with its size and SHA-256, so the corpus can
  be checked later and a changed file is noticed.
- data/ is not committed (see .gitignore): the documents have their own licences, and the PDF is big.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
UA = {"User-Agent": "course-corpus-downloader"}


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def safe_relative(path: str, prefix: str) -> str | None:
    """The part of `path` after `prefix`, or None when the path is not a plain .md file under it."""
    if not path.startswith(prefix) or not path.endswith(".md"):
        return None
    rel = path[len(prefix) :]
    parts = rel.split("/")
    if ".." in parts or rel.startswith("/") or "\\" in rel or ":" in rel:
        return None
    return rel


def download_markdown(source: dict) -> list[dict]:
    repo, sha, prefix = source["repo"], source["commit"], source["path_prefix"]
    tree = json.loads(fetch(f"https://api.github.com/repos/{repo}/git/trees/{sha}?recursive=1"))
    if tree.get("truncated"):
        sys.exit(f"{repo}: the file list was truncated; cannot continue")
    out_dir = DATA / source["id"]
    records = []
    for entry in tree["tree"]:
        if entry["type"] != "blob" or entry["path"] in source["exclude"]:
            continue
        rel = safe_relative(entry["path"], prefix)
        if rel is None:
            continue
        body = fetch(f"https://raw.githubusercontent.com/{repo}/{sha}/{entry['path']}")
        target = out_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        records.append(
            {
                "source": source["id"],
                "path": f"{source['id']}/{rel}",
                "upstream_path": entry["path"],
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
            }
        )
    print(f"{source['id']}: {len(records)} files at {repo}@{sha[:10]}")
    return records


def download_pdf(source: dict) -> list[dict]:
    out_dir = DATA / source["id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / source["url"].rsplit("/", 1)[-1]
    digest, size = hashlib.sha256(), 0
    with urllib.request.urlopen(urllib.request.Request(source["url"], headers=UA), timeout=120) as r:
        with target.open("wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
                digest.update(chunk)
                size += len(chunk)
    print(f"{source['id']}: {target.name}, {size / 1e6:.1f} MB")
    return [{"source": source["id"], "path": f"{source['id']}/{target.name}", "upstream_path": source["url"], "bytes": size, "sha256": digest.hexdigest()}]


def download_arxiv(source: dict) -> list[dict]:
    """The listed papers as PDFs. curl does the fetching (see the manifest's download_note)."""
    out_dir = DATA / source["id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for paper in source["papers"]:
        arxiv_id = paper["arxiv_id"]
        if not re.fullmatch(r"\d{4}\.\d{4,5}", arxiv_id):
            sys.exit(f"unexpected arXiv id in the manifest: {arxiv_id!r}")
        target = out_dir / f"{arxiv_id}.pdf"
        subprocess.run(
            ["curl", "-sS", "-L", "--max-time", "120", "-A", "course-corpus-downloader", "-o", str(target), paper["url"]],
            check=True,
        )
        body = target.read_bytes()
        if not body.startswith(b"%PDF-"):
            target.unlink()
            sys.exit(f"{arxiv_id}: the download is not a PDF")
        records.append({"source": source["id"], "path": f"{source['id']}/{target.name}", "upstream_path": paper["url"], "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
    total = sum(r["bytes"] for r in records)
    print(f"{source['id']}: {len(records)} papers, {total / 1e6:.1f} MB")
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", action="store_true", help="also download the large PDF source(s)")
    parser.add_argument("--papers", action="store_true", help="also download the arXiv papers")
    args = parser.parse_args()
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    index_path = DATA / "files.json"
    records: list[dict] = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else []
    for source in manifest["sources"]:
        if source["kind"] == "markdown":
            new = download_markdown(source)
        elif source["kind"] == "pdf" and args.pdf:
            new = download_pdf(source)
        elif source["kind"] == "arxiv-pdf" and args.papers:
            new = download_arxiv(source)
        else:
            continue
        records = [r for r in records if r["source"] != source["id"]] + new
    DATA.mkdir(exist_ok=True)
    index_path.write_text(json.dumps(records, indent=1), encoding="utf-8")
    print(f"{len(records)} files indexed in {index_path}")


if __name__ == "__main__":
    main()
