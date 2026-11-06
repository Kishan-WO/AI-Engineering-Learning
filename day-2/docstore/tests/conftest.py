from pathlib import Path

import pytest

from docstore import Document, DocumentStore, InMemoryStorage

SAMPLE_DOCS = Path(__file__).parent / "data" / "sample_docs"


@pytest.fixture
def sample_docs() -> Path:
    return SAMPLE_DOCS


@pytest.fixture
def python_doc() -> Document:
    return Document(title="Python basics", text="Lists and dicts", source="manual", tags=["python"])


@pytest.fixture
def fastapi_doc() -> Document:
    return Document(title="FastAPI", text="Routers and Pydantic", source="manual")


@pytest.fixture
def store(python_doc: Document, fastapi_doc: Document) -> DocumentStore:
    """An in-memory store that already holds two documents."""
    store = DocumentStore(InMemoryStorage())
    store.add(python_doc)
    store.add(fastapi_doc)
    return store
