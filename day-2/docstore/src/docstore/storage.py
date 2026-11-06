"""Storage interface and implementations for docstore."""

import json
from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from docstore.exceptions import StorageError
from docstore.models import Document


class Storage(ABC):
    """Abstract base class for document storage backends."""

    @abstractmethod
    def put(self, doc: Document) -> None:
        """Store or update a document."""

    @abstractmethod
    def get(self, doc_id: str) -> Document | None:
        """Retrieve a document by ID, or return None if not found."""

    @abstractmethod
    def delete(self, doc_id: str) -> None:
        """Remove a document by ID if it exists."""

    @abstractmethod
    def all(self) -> list[Document]:
        """Return all stored documents."""


class InMemoryStorage(Storage):
    """In-memory dictionary-backed document storage."""

    def __init__(self) -> None:
        self._docs: dict[str, Document] = {}

    def put(self, doc: Document) -> None:
        self._docs[doc.id] = doc

    def get(self, doc_id: str) -> Document | None:
        return self._docs.get(doc_id)

    def delete(self, doc_id: str) -> None:
        self._docs.pop(doc_id, None)

    def all(self) -> list[Document]:
        return list(self._docs.values())


class JsonStorage(Storage):
    """File-backed document storage using a JSON file."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def _doc_to_dict(self, doc: Document) -> dict[str, Any]:
        data = asdict(doc)
        data["created_at"] = doc.created_at.isoformat()
        return data

    def _dict_to_doc(self, data: dict[str, Any]) -> Document:
        doc_dict = dict(data)
        if isinstance(doc_dict.get("created_at"), str):
            doc_dict["created_at"] = datetime.fromisoformat(doc_dict["created_at"])
        return Document(**doc_dict)

    def _load(self) -> dict[str, Document]:
        if not self.path.exists():
            return {}
        try:
            content = self.path.read_text(encoding="utf-8")
            if not content.strip():
                return {}
            data = json.loads(content)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
            raise StorageError(f"Failed to read/parse {self.path}: {e}") from e

        try:
            if isinstance(data, list):
                return {item["id"]: self._dict_to_doc(item) for item in data}
            if isinstance(data, dict):
                return {k: self._dict_to_doc(v) for k, v in data.items()}
            return {}
        except (KeyError, TypeError, ValueError) as e:
            raise StorageError(f"Invalid document data format in {self.path}: {e}") from e

    def _save(self, docs: dict[str, Document]) -> None:
        # Write to a temp file, then swap it in, so a crash mid-write
        # never leaves a half-written (corrupt) JSON file behind.
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            data = [self._doc_to_dict(doc) for doc in docs.values()]
            tmp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp_path.replace(self.path)
        except OSError as e:
            raise StorageError(f"Failed to write to {self.path}: {e}") from e

    def put(self, doc: Document) -> None:
        docs = self._load()
        docs[doc.id] = doc
        self._save(docs)

    def get(self, doc_id: str) -> Document | None:
        return self._load().get(doc_id)

    def delete(self, doc_id: str) -> None:
        docs = self._load()
        if doc_id in docs:
            del docs[doc_id]
            self._save(docs)

    def all(self) -> list[Document]:
        return list(self._load().values())
