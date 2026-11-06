import pytest

from docstore import Document


def test_ids_are_unique_and_generated() -> None:
    a = Document(title="a", text="x", source="s")
    b = Document(title="b", text="y", source="s")
    assert a.id
    assert a.id != b.id


def test_tags_are_not_shared_between_documents() -> None:
    a = Document(title="a", text="x", source="s")
    b = Document(title="b", text="y", source="s")
    a.tags.append("only-a")
    assert b.tags == []


def test_created_at_is_timezone_aware() -> None:
    assert Document(title="a", text="x", source="s").created_at.tzinfo is not None


def test_source_is_required() -> None:
    with pytest.raises(TypeError):
        Document(title="t", text="x")  # type: ignore[call-arg]
