import logging
from pathlib import Path

import pytest

from docstore import DocumentStore, InMemoryStorage, load_folder


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    (tmp_path / "notes.txt").write_text("hello world", encoding="utf-8")
    (tmp_path / "guide.md").write_text("# Heading Title\nbody text", encoding="utf-8")
    (tmp_path / "hindi.md").write_text("# नमस्ते\nयह पाठ है", encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"\x89PNG")  # not a supported type: ignored
    (tmp_path / "subdir").mkdir()  # a directory: ignored
    return tmp_path


def test_loads_supported_files_with_titles(folder: Path) -> None:
    store = DocumentStore(InMemoryStorage())
    assert load_folder(folder, store) == 3
    assert sorted(d.title for d in store) == sorted(["notes", "Heading Title", "नमस्ते"])


def test_loading_twice_adds_nothing(folder: Path) -> None:
    store = DocumentStore(InMemoryStorage())
    load_folder(folder, store)
    assert load_folder(str(folder), store) == 0  # a str path works too
    assert len(store) == 3


def test_non_utf8_file_is_skipped_with_a_warning(
    folder: Path, caplog: pytest.LogCaptureFixture
) -> None:
    store = DocumentStore(InMemoryStorage())
    load_folder(folder, store)
    (folder / "broken.txt").write_bytes(b"\xff\xfe bad bytes")
    with caplog.at_level(logging.WARNING):
        assert load_folder(folder, store) == 0
    assert "not valid UTF-8" in caplog.text
    assert len(store) == 3


def test_markdown_without_a_heading_uses_the_file_name(tmp_path: Path) -> None:
    (tmp_path / "checklist.md").write_text("## only a level-two heading\ntext", encoding="utf-8")
    store = DocumentStore(InMemoryStorage())
    load_folder(tmp_path, store)
    assert [d.title for d in store] == ["checklist"]


def test_the_50_sample_documents(sample_docs: Path) -> None:
    store = DocumentStore(InMemoryStorage())
    assert load_folder(sample_docs, store) == 50
    titles = {Path(d.source).name: d.title for d in store}
    assert titles["code-review-checklist.md"] == "code-review-checklist"  # only ## headings
    assert titles["healthy-sleep.md"] == "Healthy Sleep Habits"  # blank lines before heading
    assert titles["solar-system.txt"] == "solar-system"  # .txt uses the stem
    assert [d.title for d in store.search("monsoon")] == ["indian-monsoon"]
