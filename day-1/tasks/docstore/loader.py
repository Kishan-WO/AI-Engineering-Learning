"""Loader utilities to import files into a DocumentStore."""

import logging
from pathlib import Path

from docstore.models import Document
from docstore.store import DocumentStore

logger = logging.getLogger(__name__)

SUPPORTED_SUFFIXES = {".txt", ".md"}


def _title_for(file_path: Path, text: str) -> str:
    """Return the first '# ' heading of a markdown file, otherwise the file stem."""
    if file_path.suffix.lower() == ".md":
        for line in text.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    return file_path.stem


def load_folder(folder: Path | str, store: DocumentStore) -> int:
    """Load all .txt and .md files from a directory into the document store.

    For markdown (.md) files, the title is extracted from the first line starting
    with '# '. If no such heading exists, or for .txt files, the file stem is used.
    Source is recorded as the string path of the file.

    Files already in the store (same source) are skipped, so loading the same
    folder twice does not create duplicates. Files that are not valid UTF-8 are
    skipped with a warning.

    Returns the count of files newly loaded.
    """
    folder_path = Path(folder)
    existing_sources = {doc.source for doc in store}
    count = 0

    files = sorted(
        p
        for p in folder_path.glob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
    )

    for file_path in files:
        source = str(file_path)
        if source in existing_sources:
            continue

        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.warning("Skipping %s: not valid UTF-8", file_path)
            continue

        store.add(Document(title=_title_for(file_path, text), text=text, source=source))
        existing_sources.add(source)
        count += 1

    return count
