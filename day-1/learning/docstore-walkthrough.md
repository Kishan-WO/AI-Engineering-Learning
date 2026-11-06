# The Day 1 `docstore` project, file by file

Question: explain the whole project step by step, how to run it, how to see the JSON file, and how to try search and add.

The project is a small **document-store library**: it keeps documents (title, text, source, tags) in memory or in a JSON file, and can load `.txt` and `.md` files from a folder.

```
docstore/
  exceptions.py   the error classes
  models.py       the Document dataclass
  storage.py      Storage (abstract), InMemoryStorage, JsonStorage
  store.py        DocumentStore (the public API)
  loader.py       load_folder(...)
  __init__.py     what the package exports
test_docstore.py  tests with plain asserts
save_docs.py      loads sample_docs/ into docs.json
sample_docs/      50 English files
```

## 1. `exceptions.py`: a small hierarchy
```python
class DocStoreError(Exception): ...
class DocumentNotFoundError(DocStoreError): ...
class DuplicateDocumentError(DocStoreError): ...
class StorageError(DocStoreError): ...
```
One base class, so a caller can catch `DocStoreError` for anything from this library, or a specific subclass.

## 2. `models.py`: the `Document` dataclass
```python
@dataclass(kw_only=True)
class Document:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    text: str
    source: str
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```
- `@dataclass` writes `__init__`, `__repr__` and `__eq__` for me.
- `kw_only=True`: fields are passed by name. That also lets `id` (which has a default) come before fields without one.
- `default_factory` builds a **new** value for every object: a new UUID, a new empty list, the current time. A plain `tags: list[str] = []` would share one list between all documents (a dataclass refuses it).
- `source` is required: every document says where it came from.
- `timezone.utc` makes the timestamp timezone-aware.

## 3. `storage.py`: the storage layer
`Storage` is an **abstract base class** (`ABC`) that lists four methods every storage must have: `put`, `get`, `delete`, `all`. It cannot be created itself; a subclass that misses a method cannot be created either.

**`InMemoryStorage`** keeps a `dict` of id → Document. Fast, gone when the program ends.

**`JsonStorage`** keeps a JSON file:
- `_doc_to_dict` / `_dict_to_doc` convert a Document to and from plain data. The datetime is written as an ISO string (`created_at.isoformat()`) and read back with `datetime.fromisoformat`.
- `_load` reads the whole file. A missing or empty file means "no documents". A broken file raises `StorageError(...) from e`, which keeps the original error as the cause.
- `_save` writes to a **temporary file first and then replaces the real one**, so a crash in the middle never leaves half a JSON file.
- `put`, `delete` and friends do load → change → save.

## 4. `store.py`: `DocumentStore`
```python
class DocumentStore:
    def __init__(self, storage: Storage) -> None:
        self.storage = storage
```
- **Composition**: the store *has* a storage; it does not inherit from one. Pass `InMemoryStorage()` or `JsonStorage("docs.json")` and the store works the same.
- `add` raises `DuplicateDocumentError` if the id exists. `get` and `delete` raise `DocumentNotFoundError` if it does not.
- `search(keyword)` is a case-insensitive match on title or text, as a list comprehension.
- Dunder methods make it feel like a collection: `len(store)`, `for doc in store`, `doc_id in store`. `__contains__` accepts any object and returns `False` for non-strings.

## 5. `loader.py`: `load_folder(folder, store)`
- Only `.txt` and `.md` files are read (`SUPPORTED_SUFFIXES`).
- A markdown file's title is its first `# Heading`; otherwise the file name without extension.
- The `source` is the file path. Files whose source is already in the store are **skipped**, so running it twice adds nothing.
- A file that is not valid UTF-8 is skipped with a warning and does not stop the run.
- It returns how many files it added.

## 6. `__init__.py`
Imports the public names and lists them in `__all__`, so users write `from docstore import DocumentStore, JsonStorage` (see `modules-packages-and-all.md`).

## 7. How to run it
From the `day-1` folder:
```bash
uv run python test_docstore.py      # all the checks; prints "all docstore tests passed"
uv run python save_docs.py          # loads sample_docs/ into docs.json and searches "python"
```

## 8. See the JSON file
`docs.json` is created next to where the script ran.
- Open it in the editor (VS Code: right-click → Format Document makes it readable).
- Or print it from the terminal:
  ```bash
  uv run python -m json.tool docs.json | head -40
  ```
Each document is an object with `id`, `title`, `text`, `source`, `tags` and `created_at` (ISO text).

## 9. Try add and search yourself
Start a Python prompt in `day-1` (`uv run python`) and type:
```python
from docstore import Document, DocumentStore, JsonStorage

store = DocumentStore(JsonStorage("docs.json"))
store.add(Document(title="My note", text="learning python today", source="manual", tags=["demo"]))
len(store)
[d.title for d in store.search("python")]
store.get(store.search("python")[0].id).tags
```
A new `store` over the same file sees everything that was saved earlier.

## Quick check
- Why does `Document` use `default_factory` for `tags`?
- What is the difference between `Storage`, `InMemoryStorage` and `JsonStorage`?
- Why does `DocumentStore` take a storage object instead of inheriting from one?
- How does `JsonStorage._save` avoid leaving a half-written file?
- Why can `load_folder` be run twice without creating duplicates?
