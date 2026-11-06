"""Command-line interface for docstore.

    docstore load ./sample_docs
    docstore list
    docstore search python
    docstore get <id>
    docstore delete <id>
    docstore count

The JSON file is `docs.json` in the current folder, or --store / $DOCSTORE_PATH.
"""

from pathlib import Path
from typing import Annotated, NoReturn

import typer

from docstore import DocStoreError, DocumentStore, JsonStorage, load_folder

app = typer.Typer(help="A small document store.", no_args_is_help=True)

StoreOption = Annotated[
    Path,
    typer.Option("--store", "-s", envvar="DOCSTORE_PATH", help="JSON file holding the documents."),
]


def open_store(path: Path) -> DocumentStore:
    return DocumentStore(JsonStorage(path))


def fail(error: DocStoreError) -> NoReturn:
    """Print a docstore error to stderr and exit with status 1."""
    typer.echo(f"Error: {error}", err=True)
    raise typer.Exit(code=1)


@app.command()
def load(
    folder: Annotated[
        Path,
        typer.Argument(
            exists=True, file_okay=False, readable=True, help="Folder of .txt/.md files."
        ),
    ],
    store: StoreOption = Path("docs.json"),
) -> None:
    """Load every .txt and .md file in FOLDER (files already loaded are skipped)."""
    try:
        docs = open_store(store)
        added = load_folder(folder, docs)
        total = len(docs)
    except DocStoreError as error:
        fail(error)
    typer.echo(f"Added {added} documents ({total} in {store}).")


@app.command("list")
def list_docs(
    store: StoreOption = Path("docs.json"),
    limit: Annotated[int, typer.Option(min=1, help="Show at most this many.")] = 20,
) -> None:
    """List documents as 'id  title'."""
    try:
        docs = list(open_store(store))
    except DocStoreError as error:
        fail(error)
    for doc in docs[:limit]:
        typer.echo(f"{doc.id}  {doc.title}")
    if len(docs) > limit:
        typer.echo(f"... and {len(docs) - limit} more")


@app.command()
def search(keyword: str, store: StoreOption = Path("docs.json")) -> None:
    """Find documents whose title or text contains KEYWORD (case-insensitive)."""
    try:
        results = open_store(store).search(keyword)
    except DocStoreError as error:
        fail(error)
    for doc in results:
        typer.echo(f"{doc.id}  {doc.title}")
    typer.echo(f"{len(results)} found.")


@app.command()
def get(doc_id: str, store: StoreOption = Path("docs.json")) -> None:
    """Show one document."""
    try:
        doc = open_store(store).get(doc_id)
    except DocStoreError as error:
        fail(error)
    typer.echo(f"id:      {doc.id}")
    typer.echo(f"title:   {doc.title}")
    typer.echo(f"source:  {doc.source}")
    typer.echo(f"tags:    {', '.join(doc.tags) or '-'}")
    typer.echo(f"created: {doc.created_at.isoformat()}")
    typer.echo("")
    typer.echo(doc.text)


@app.command()
def delete(doc_id: str, store: StoreOption = Path("docs.json")) -> None:
    """Delete one document."""
    try:
        open_store(store).delete(doc_id)
    except DocStoreError as error:
        fail(error)
    typer.echo(f"Deleted {doc_id}.")


@app.command()
def count(store: StoreOption = Path("docs.json")) -> None:
    """Print how many documents are stored."""
    try:
        total = len(open_store(store))
    except DocStoreError as error:
        fail(error)
    typer.echo(str(total))
