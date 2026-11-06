import json
from pathlib import Path

import pytest

from docstore import Document, DocumentStore, InMemoryStorage, JsonStorage, StorageError


def test_in_memory_put_get_delete_all(python_doc: Document) -> None:
    storage = InMemoryStorage()
    storage.put(python_doc)
    assert storage.get(python_doc.id) == python_doc
    assert storage.all() == [python_doc]
    storage.delete(python_doc.id)
    storage.delete(python_doc.id)  # deleting twice is fine
    assert storage.get(python_doc.id) is None


def test_json_storage_keeps_data_between_instances(tmp_path: Path, python_doc: Document) -> None:
    path = tmp_path / "docs.json"
    DocumentStore(JsonStorage(path)).add(python_doc)
    reloaded = DocumentStore(JsonStorage(path))  # a new instance, same file
    assert reloaded.get(python_doc.id) == python_doc  # all fields survive, including the datetime


def test_json_storage_accepts_a_string_path(tmp_path: Path, python_doc: Document) -> None:
    storage = JsonStorage(str(tmp_path / "docs.json"))
    storage.put(python_doc)
    assert storage.all() == [python_doc]


def test_json_storage_delete_updates_the_file(tmp_path: Path, python_doc: Document) -> None:
    storage = JsonStorage(tmp_path / "docs.json")
    storage.put(python_doc)
    storage.delete("not-there")  # nothing to delete: no error
    storage.delete(python_doc.id)
    assert storage.all() == []


def test_json_storage_creates_missing_parent_folders(tmp_path: Path, python_doc: Document) -> None:
    storage = JsonStorage(tmp_path / "a" / "b" / "docs.json")
    storage.put(python_doc)
    assert storage.get(python_doc.id) == python_doc


def test_json_storage_leaves_no_temp_file(tmp_path: Path, python_doc: Document) -> None:
    DocumentStore(JsonStorage(tmp_path / "docs.json")).add(python_doc)
    assert [p.name for p in tmp_path.iterdir()] == ["docs.json"]


def test_missing_and_empty_files_mean_no_documents(tmp_path: Path) -> None:
    assert JsonStorage(tmp_path / "missing.json").all() == []
    empty = tmp_path / "empty.json"
    empty.write_text("   \n", encoding="utf-8")
    assert JsonStorage(empty).all() == []


def test_invalid_json_raises_storage_error_with_cause(tmp_path: Path) -> None:
    path = tmp_path / "docs.json"
    path.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(StorageError) as info:
        JsonStorage(path).all()
    assert isinstance(info.value.__cause__, json.JSONDecodeError)


def test_json_that_is_not_utf8_raises_storage_error(tmp_path: Path) -> None:
    path = tmp_path / "docs.json"
    path.write_bytes(b"\xff\xfe\x00bad")
    with pytest.raises(StorageError):
        JsonStorage(path).all()


def test_wrong_document_shape_raises_storage_error(tmp_path: Path) -> None:
    path = tmp_path / "docs.json"
    path.write_text(json.dumps([{"id": "1", "unexpected": True}]), encoding="utf-8")
    with pytest.raises(StorageError):
        JsonStorage(path).all()


def test_dict_format_and_unrelated_json_values(tmp_path: Path, python_doc: Document) -> None:
    saved = JsonStorage(tmp_path / "list.json")
    saved.put(python_doc)
    as_list = json.loads((tmp_path / "list.json").read_text(encoding="utf-8"))

    as_dict = tmp_path / "dict.json"
    as_dict.write_text(json.dumps({python_doc.id: as_list[0]}), encoding="utf-8")
    assert JsonStorage(as_dict).all() == [python_doc]

    number = tmp_path / "number.json"
    number.write_text("42", encoding="utf-8")
    assert JsonStorage(number).all() == []


def test_write_failure_raises_storage_error(tmp_path: Path, python_doc: Document) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("a file, not a folder", encoding="utf-8")
    with pytest.raises(StorageError):
        JsonStorage(blocker / "docs.json").put(python_doc)
