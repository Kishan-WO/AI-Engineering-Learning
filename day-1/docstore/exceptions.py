"""Custom exceptions for docstore."""


class DocStoreError(Exception):
    """Base exception for all docstore errors."""


class DocumentNotFoundError(DocStoreError):
    """Raised when a requested document does not exist in the store."""


class DuplicateDocumentError(DocStoreError):
    """Raised when attempting to add a document with an ID that already exists."""


class StorageError(DocStoreError):
    """Raised when an underlying storage error occurs (e.g., corrupt JSON or I/O failure)."""
