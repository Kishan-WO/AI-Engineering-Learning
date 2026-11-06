from pathlib import Path

import pytest
from typer.testing import CliRunner

from docstore.cli import app

runner = CliRunner()


@pytest.fixture
def db(tmp_path: Path) -> str:
    return str(tmp_path / "docs.json")


@pytest.fixture
def loaded(db: str, sample_docs: Path) -> str:
    result = runner.invoke(app, ["load", str(sample_docs), "--store", db])
    assert result.exit_code == 0, result.output
    return db


def first_id(db: str) -> str:
    result = runner.invoke(app, ["list", "--store", db, "--limit", "1"])
    return result.output.split()[0]


def test_no_arguments_shows_help() -> None:
    result = runner.invoke(app, [])
    assert "Usage" in result.output
    assert "load" in result.output


def test_load_then_count(db: str, sample_docs: Path) -> None:
    result = runner.invoke(app, ["load", str(sample_docs), "-s", db])
    assert result.exit_code == 0
    assert "Added 50 documents" in result.output
    again = runner.invoke(app, ["load", str(sample_docs), "-s", db])
    assert "Added 0 documents" in again.output  # loading twice adds nothing
    assert runner.invoke(app, ["count", "-s", db]).output.strip() == "50"


def test_load_a_missing_folder_is_a_usage_error(db: str, tmp_path: Path) -> None:
    result = runner.invoke(app, ["load", str(tmp_path / "nope"), "-s", db])
    assert result.exit_code == 2


def test_list_limits_the_output(loaded: str) -> None:
    result = runner.invoke(app, ["list", "-s", loaded, "--limit", "5"])
    assert result.exit_code == 0
    assert "... and 45 more" in result.output
    assert len(result.output.strip().splitlines()) == 6


def test_list_with_everything_shown_has_no_more_line(loaded: str) -> None:
    result = runner.invoke(app, ["list", "-s", loaded, "--limit", "100"])
    assert "more" not in result.output


def test_search(loaded: str) -> None:
    result = runner.invoke(app, ["search", "monsoon", "-s", loaded])
    assert result.exit_code == 0
    assert "indian-monsoon" in result.output
    assert "1 found." in result.output


def test_get_shows_the_fields(loaded: str) -> None:
    result = runner.invoke(app, ["get", first_id(loaded), "-s", loaded])
    assert result.exit_code == 0
    for label in ("id:", "title:", "source:", "tags:", "created:"):
        assert label in result.output


def test_get_a_missing_id_fails_with_a_message(loaded: str) -> None:
    result = runner.invoke(app, ["get", "missing", "-s", loaded])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_delete(loaded: str) -> None:
    doc_id = first_id(loaded)
    assert runner.invoke(app, ["delete", doc_id, "-s", loaded]).exit_code == 0
    assert runner.invoke(app, ["count", "-s", loaded]).output.strip() == "49"
    assert runner.invoke(app, ["delete", doc_id, "-s", loaded]).exit_code == 1


def test_a_corrupt_file_is_reported_not_a_traceback(tmp_path: Path) -> None:
    bad = tmp_path / "docs.json"
    bad.write_text("{not json", encoding="utf-8")
    for command in (["count"], ["list"], ["search", "x"], ["get", "x"], ["delete", "x"]):
        result = runner.invoke(app, [*command, "-s", str(bad)])
        assert result.exit_code == 1, command
        assert "Error:" in result.output


def test_load_into_a_corrupt_file_fails(tmp_path: Path, sample_docs: Path) -> None:
    bad = tmp_path / "docs.json"
    bad.write_text("{not json", encoding="utf-8")
    result = runner.invoke(app, ["load", str(sample_docs), "-s", str(bad)])
    assert result.exit_code == 1


def test_the_store_path_can_come_from_the_environment(
    tmp_path: Path, sample_docs: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DOCSTORE_PATH", str(tmp_path / "from-env.json"))
    assert runner.invoke(app, ["load", str(sample_docs)]).exit_code == 0
    assert (tmp_path / "from-env.json").exists()
