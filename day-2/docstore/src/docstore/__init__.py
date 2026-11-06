"""docstore - a small typed document store."""

from docstore.exceptions import (
    DocStoreError,
    DocumentNotFoundError,
    DuplicateDocumentError,
    StorageError,
)
from docstore.loader import load_folder
from docstore.models import Document
from docstore.storage import InMemoryStorage, JsonStorage, Storage
from docstore.store import DocumentStore

__all__ = [
    "DocStoreError",
    "Document",
    "DocumentNotFoundError",
    "DocumentStore",
    "DuplicateDocumentError",
    "InMemoryStorage",
    "JsonStorage",
    "Storage",
    "StorageError",
    "load_folder",
]
