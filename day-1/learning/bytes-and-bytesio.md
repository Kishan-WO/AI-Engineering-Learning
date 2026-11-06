# `bytes`, `str` and `io.BytesIO`

Where I met it: `reader = PdfReader(io.BytesIO(data))` in the document upload code.

## 1. `str` vs `bytes`
| | `str` | `bytes` |
|---|---|---|
| Holds | Text: characters | Raw bytes (numbers 0 to 255) |
| Example | `"नमस्ते"` | `b'\xe0\xa4\xa8...'` |
| Convert | `text.encode("utf-8")` gives bytes | `data.decode("utf-8")` gives text |

A file, a network message or an uploaded PDF is always **bytes**. Text is only the bytes read with an encoding.

Real example with Hindi:
```
str len: 6 | bytes len: 18 | first bytes: b'\xe0\xa4\xa8\xe0\xa4\xae'
```
Six characters need 18 bytes in UTF-8, because each Devanagari character takes 3 bytes. (English letters take 1.)

JavaScript comparison: `bytes` is like a `Buffer` / `Uint8Array`; `str` is a string.

## 2. The problem
Many libraries want a **file object**, something with `.read()`, `.seek()` and `.tell()`. But my uploaded data is just a `bytes` value in memory. I don't want to write a temp file to disk only to read it back.

## 3. `io.BytesIO`: a file made of memory
`io.BytesIO(data)` wraps bytes in an object that **behaves like an open binary file**:

```python
import io
data = "नमस्ते".encode("utf-8")
buf = io.BytesIO(data)

buf.read(6)        # b'\xe0\xa4\xa8\xe0\xa4\xae'   first 6 bytes
buf.tell()         # 6                              current position
buf.read()         # the rest
buf.seek(0)        # go back to the start
buf.read().decode("utf-8")   # 'नमस्ते'
```
- It lives entirely in RAM: no disk, no cleanup, fast.
- It has a **position**: reading moves it forward; `seek(0)` rewinds.
- Its text twin is `io.StringIO` for `str`.

JavaScript comparison: a `Buffer` wrapped in a readable stream.

## 4. How the PDF code uses it
```python
reader = PdfReader(io.BytesIO(data))
pages = [page.extract_text() for page in reader.pages]
```
- `data` is the whole uploaded file as bytes.
- `PdfReader` expects a path or a file-like object. `BytesIO` lets it read straight from memory.
- No file is written. Nothing to delete afterwards.

## 5. When not to use it
- **Very large data**: everything sits in RAM. The upload code limits the size (20 MB) before this point.
- **When a path already exists**: just pass the path.

## Common mistakes
| Mistake | What happens |
|---|---|
| Passing `str` to `BytesIO` | `TypeError`: it needs bytes |
| Reading twice without `seek(0)` | The second read returns empty bytes |
| Forgetting to decode before treating bytes as text | You get `b'...'` objects, not strings |
| Counting `len(text)` for storage size | Characters ≠ bytes; use `len(text.encode("utf-8"))` |

## Quick check
- Why is a Hindi string 6 characters but 18 bytes?
- What does `io.BytesIO(data)` give me?
- What does `seek(0)` do?
- Why is it better than writing a temporary file for a PDF held in memory?
