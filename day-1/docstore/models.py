"""Document data model."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid


@dataclass(kw_only=True)
class Document:
    """Represents a document in the store with its metadata.

    kw_only=True lets `id` (which has a default) come before the required fields.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    text: str
    source: str
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
