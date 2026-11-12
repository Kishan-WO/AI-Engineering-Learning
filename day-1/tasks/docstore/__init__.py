"""docstore package - A lightweight document store library."""

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
    "DocumentNotFoundError",
    "DuplicateDocumentError",
    "StorageError",
    "Document",
    "Storage",
    "InMemoryStorage",
    "JsonStorage",
    "DocumentStore",
    "load_folder",
]
