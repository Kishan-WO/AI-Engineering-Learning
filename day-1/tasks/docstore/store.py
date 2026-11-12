"""High-level DocumentStore managing storage and business logic."""

from collections.abc import Iterator

from docstore.exceptions import DocumentNotFoundError, DuplicateDocumentError
from docstore.models import Document
from docstore.storage import Storage


class DocumentStore:
    """Document store providing high-level CRUD, search, and container operations."""

    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    def add(self, doc: Document) -> None:
        """Add a new document to the store.

        Raises DuplicateDocumentError if a document with the same ID already exists.
        """
        if self.storage.get(doc.id) is not None:
            raise DuplicateDocumentError(f"Document with id '{doc.id}' already exists.")
        self.storage.put(doc)

    def get(self, doc_id: str) -> Document:
        """Retrieve a document by ID.

        Raises DocumentNotFoundError if the document does not exist.
        """
        doc = self.storage.get(doc_id)
        if doc is None:
            raise DocumentNotFoundError(f"Document with id '{doc_id}' not found.")
        return doc

    def delete(self, doc_id: str) -> None:
        """Delete a document by ID.

        Raises DocumentNotFoundError if the document does not exist.
        """
        if self.storage.get(doc_id) is None:
            raise DocumentNotFoundError(f"Document with id '{doc_id}' not found.")
        self.storage.delete(doc_id)

    def search(self, keyword: str) -> list[Document]:
        """Search documents by keyword across title or text (case-insensitive)."""
        keyword_lower = keyword.lower()
        return [
            doc
            for doc in self.storage.all()
            if keyword_lower in doc.title.lower() or keyword_lower in doc.text.lower()
        ]

    def __len__(self) -> int:
        return len(self.storage.all())

    def __iter__(self) -> Iterator[Document]:
        return iter(self.storage.all())

    def __contains__(self, doc_id: object) -> bool:
        # `in` can be given any object, so accept object and reject non-strings.
        return isinstance(doc_id, str) and self.storage.get(doc_id) is not None
