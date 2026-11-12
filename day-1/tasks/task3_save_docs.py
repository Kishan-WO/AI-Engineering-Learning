"""Day 1, task 3: load the 50 sample documents into a JSON store, then search it.

    uv run python tasks/task3_save_docs.py
"""

from pathlib import Path

from docstore import DocumentStore, JsonStorage, load_folder

DAY_1 = Path(__file__).parent.parent
STORE_FILE = DAY_1 / "results" / "docs.json"
SAMPLE_DOCS = DAY_1 / "data" / "sample_docs"

STORE_FILE.parent.mkdir(exist_ok=True)
store = DocumentStore(JsonStorage(STORE_FILE))
added = load_folder(SAMPLE_DOCS, store)
print(f"added {added} documents, {len(store)} in {STORE_FILE.relative_to(DAY_1)}")

results = store.search("python")
print("Found", len(results), "results")

for r in results[:]:
    print("   ", r.source, " | ", r.title)
