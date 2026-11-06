from pathlib import Path

from docstore import DocumentStore, JsonStorage, load_folder

store = DocumentStore(JsonStorage("docs.json"))
added = load_folder(Path("sample_docs"), store)
print(f"added {added} documents, {len(store)} in docs.json")

results = store.search("python")
print("Found", len(results), "results")

for r in results[:]:
    print("   ", r.source, " | ", r.title)