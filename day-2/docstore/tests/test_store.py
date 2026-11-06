import pytest

from docstore import (
    DocStoreError,
    Document,
    DocumentNotFoundError,
    DocumentStore,
    DuplicateDocumentError,
    InMemoryStorage,
)


def test_len_contains_and_get(store: DocumentStore, python_doc: Document) -> None:
    assert len(store) == 2
    assert python_doc.id in store
    assert "missing" not in store
    assert store.get(python_doc.id) == python_doc


def test_iteration_yields_every_document(
    store: DocumentStore, python_doc: Document, fastapi_doc: Document
) -> None:
    assert {d.id for d in store} == {python_doc.id, fastapi_doc.id}


def test_contains_with_a_non_string_never_crashes() -> None:
    assert 5 not in DocumentStore(InMemoryStorage())


@pytest.mark.parametrize(
    ("keyword", "expected_title"),
    [
        ("PYTHON", "Python basics"),  # case-insensitive, matches the title
        ("pydantic", "FastAPI"),  # matches the text
    ],
)
def test_search_finds_documents(store: DocumentStore, keyword: str, expected_title: str) -> None:
    assert [d.title for d in store.search(keyword)] == [expected_title]


def test_search_with_no_match_is_empty(store: DocumentStore) -> None:
    assert store.search("nothing") == []


def test_adding_a_duplicate_id_raises(store: DocumentStore, python_doc: Document) -> None:
    with pytest.raises(DuplicateDocumentError):
        store.add(python_doc)


def test_get_missing_raises_part_of_the_hierarchy(store: DocumentStore) -> None:
    with pytest.raises(DocumentNotFoundError) as info:
        store.get("missing")
    assert isinstance(info.value, DocStoreError)


def test_delete_removes_once_then_raises(store: DocumentStore, fastapi_doc: Document) -> None:
    store.delete(fastapi_doc.id)
    assert len(store) == 1
    with pytest.raises(DocumentNotFoundError):
        store.delete(fastapi_doc.id)
