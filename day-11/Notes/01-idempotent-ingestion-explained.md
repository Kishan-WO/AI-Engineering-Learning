# Idempotent ingestion explained

Goes with `learning/4.ingestion-engineering.md`, sections 3 and 4. "Idempotent" means: doing it twice has the same effect as doing it once. This note shows what that looks like in code and why one hash is not enough.

## 1. Three hashes, three questions
| Hash | Computed from | Question it answers | Where it lives |
|---|---|---|---|
| **File hash** (`content_hash`) | the bytes of the uploaded file | have I already got this exact file for this tenant? | `documents`, unique with `tenant_id` |
| **Chunk ID** | document id, pipeline version, position, chunk text | is this exact chunk already stored? | primary key of `chunks` |
| **Pipeline version** | parser, chunker settings, header option, embedding model | was this document produced by today's pipeline? | a column on `chunks` and on the document |

Each hash answers a different question, so I need all three. The file hash alone says nothing about a changed chunker; the chunk ID alone does not stop me from parsing a duplicate file.

## 2. The flow, step by step
```
upload file
  -> sha256(bytes) = content_hash
  -> (tenant_id, content_hash) already in documents?
        yes, and its pipeline version is current -> point to the existing document, enqueue nothing
        yes, but the version is old               -> enqueue a re-ingest job
        no                                        -> insert the document, enqueue an ingest job
worker
  -> parse, clean, chunk
  -> chunk_id = sha256(document_id | pipeline_version | position | text)
  -> embed the chunks (skip texts already in the embedding cache)
  -> in ONE transaction:
        delete the chunks of this document that are not in the new set   (first)
        upsert the new chunks by chunk_id
  -> set job status = succeeded
```

## 3. Why the chunk ID includes the position and the text
- **Only the text:** two identical paragraphs in one document (a repeated disclaimer) would get the same ID and one would overwrite the other.
- **Only the position:** if one paragraph is inserted at the top, every chunk moves one position and every ID changes, although most text did not change.
- **Both:** the same input gives the same ID (idempotent), and any real change gives a new ID. The delete step removes the old IDs of that document.
- A later improvement can make IDs survive an insertion by using the text and heading path without the position. The price is handling real duplicates. I note it as a choice, not as the answer.

## 4. Why "delete the ones not in the new set" is the key line, and why it comes first
Upsert by chunk ID only adds new IDs and overwrites equal ones. If a new chunker gives every chunk a new ID, the old rows stay. Search then returns old and new chunks together, which is the duplicate problem again in a new form. Deleting the document's IDs that are not in the new set, in the same transaction as the upsert, fixes it, and a failure in the middle leaves the old set intact.

**The order matters in my table.** `chunks` has `UNIQUE (document_id, chunk_index)`. A changed chunk has a new ID but the same position, so inserting it while the old row is still there breaks that constraint. I tested it in my local PostgreSQL, on a temporary table with the same two keys, and rolled it back:
```
insert the new ID first, ON CONFLICT (id) DO UPDATE
  -> ERROR:  duplicate key value violates unique constraint "c_document_id_chunk_index_key"
     DETAIL:  Key (document_id, chunk_index)=(1, 0) already exists.

delete first, then insert (same transaction)  -> new-id | new text
roll the transaction back                     -> old-id | old text   (nothing was lost)
```
`ON CONFLICT (id)` handles only a clash of IDs, not of the other unique key. A chunk that keeps its ID also keeps its position (the position is part of the ID), so it does not clash after the delete.

The Day 10 loader (`scripts/upsert_corpus.py`) works differently: it upserts on `(document_id, chunk_index)` and deletes nothing. That is enough for loading the same sections again, but a chunker that made fewer chunks would leave the higher positions behind.

## 5. The proof for task 6
1. Ingest the corpus. Record: number of documents, number of chunks, a hash of the sorted chunk IDs, a hash of the sorted chunk texts.
2. Ingest it again (same files).
3. Record the same four numbers. They must be identical, and the job log must say that nothing was re-processed.
4. Change one setting (for example the overlap), re-ingest, and check that the old chunks of every document are gone and that `chunks` has no document with two pipeline versions.

## 6. What to remember
- Idempotency is a property I test with numbers before and after, not a feeling.
- A unique constraint is my last line of defence; the checks in the code are the first.
- After a chunker change the question is not "is it a duplicate?" but "which version is current?".
