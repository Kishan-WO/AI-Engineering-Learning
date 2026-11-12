import json
import tempfile
from pathlib import Path

from docstore import (
    DocStoreError,
    Document,
    DocumentNotFoundError,
    DocumentStore,
    DuplicateDocumentError,
    InMemoryStorage,
    JsonStorage,
    StorageError,
    load_folder,
)


def expect_raises(exc_type, fn, *args):
    """Assert that fn(*args) raises exc_type, and return the exception."""
    try:
        fn(*args)
    except exc_type as e:
        return e
    raise AssertionError(f"expected {exc_type.__name__}")


# --- Document ---
doc = Document(title="Python basics", text="Lists and dicts", source="manual", tags=["python"])
d2 = Document(title="FastAPI", text="Routers and Pydantic", source="manual")
assert doc.id and doc.id != d2.id                          # unique auto-generated ids
assert d2.tags == []
assert d2.tags is not Document(title="a", text="b", source="c").tags   # no shared mutable default
assert doc.created_at.tzinfo is not None                   # timezone-aware

# --- DocumentStore with in-memory storage ---
store = DocumentStore(InMemoryStorage())
store.add(doc)
store.add(d2)
assert len(store) == 2
assert doc.id in store and "missing" not in store
assert store.get(doc.id) == doc
assert {d.id for d in store} == {doc.id, d2.id}
assert store.search("PYTHON") == [doc]                     # case-insensitive, matches the title
assert store.search("pydantic") == [d2]                    # matches the text
assert store.search("nothing") == []

expect_raises(DuplicateDocumentError, store.add, doc)
e = expect_raises(DocumentNotFoundError, store.get, "missing")
assert isinstance(e, DocStoreError)                        # part of the hierarchy
store.delete(d2.id)
assert len(store) == 1
expect_raises(DocumentNotFoundError, store.delete, d2.id)

# --- JsonStorage keeps data between instances ---
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "docs.json"
    DocumentStore(JsonStorage(path)).add(doc)
    reloaded = DocumentStore(JsonStorage(path))            # a new instance, same file
    assert reloaded.get(doc.id) == doc                     # all fields survive, including the datetime

    path.write_text("{not valid json", encoding="utf-8")
    e = expect_raises(StorageError, lambda: len(DocumentStore(JsonStorage(path))))
    assert isinstance(e.__cause__, json.JSONDecodeError)   # raise ... from e

# --- load_folder ---
with tempfile.TemporaryDirectory() as tmp:
    folder = Path(tmp)
    (folder / "notes.txt").write_text("hello world", encoding="utf-8")
    (folder / "guide.md").write_text("# Heading Title\nbody text", encoding="utf-8")
    (folder / "hindi.md").write_text("# नमस्ते\nयह पाठ है", encoding="utf-8")
    (folder / "image.png").write_bytes(b"\x89PNG")       # should be ignored

    store = DocumentStore(InMemoryStorage())
    assert load_folder(folder, store) == 3
    assert sorted(d.title for d in store) == sorted(["notes", "Heading Title", "नमस्ते"])

    # loading the same folder again adds nothing
    assert load_folder(folder, store) == 0
    assert len(store) == 3

    # a file that isn't valid UTF-8 is skipped, not fatal
    (folder / "broken.txt").write_bytes(b"\xff\xfe bad bytes")
    assert load_folder(folder, store) == 0
    assert len(store) == 3

# --- Document requires a source ---
# on purpose: the call has no `source`, and the test proves it raises TypeError (so the checker's warning is expected)
expect_raises(TypeError, lambda: Document(title="t", text="x"))  # type: ignore[call-arg]

# --- `in` with a non-string never crashes ---
assert 5 not in DocumentStore(InMemoryStorage())

# --- JsonStorage leaves no temp file behind ---
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "docs.json"
    DocumentStore(JsonStorage(path)).add(doc)
    assert [p.name for p in Path(tmp).iterdir()] == ["docs.json"]

# --- the 50 sample documents ---
sample = DocumentStore(InMemoryStorage())
assert load_folder(Path(__file__).parent.parent / "data" / "sample_docs", sample) == 50
titles = {Path(d.source).name: d.title for d in sample}
assert titles["code-review-checklist.md"] == "code-review-checklist"   # only ## headings
assert titles["healthy-sleep.md"] == "Healthy Sleep Habits"            # blank lines before heading
assert titles["solar-system.txt"] == "solar-system"                    # .txt uses the stem
assert [d.title for d in sample.search("monsoon")] == ["indian-monsoon"]

print("all docstore tests passed")
