def chunk_words(text: str, size: int, overlap: int = 0) -> list[str]:
    if size <= 0:
        raise ValueError(f"size must be positive, got {size}")
    if overlap < 0:
        raise ValueError(f"overlap must be non-negative, got {overlap}")
    if overlap >= size:
        raise ValueError(f"overlap ({overlap}) must be smaller than size ({size})")
    chars = text.split()
    if not chars:
        return []
    chunks = []
    for i in range(0, len(chars), size - overlap):
        chunk = chars[i:i + size]
        chunks.append(" ".join(chunk))
        if (i+size) >= len(chars):
            break
    return chunks

### =============== TESTING ===============

# basic
assert chunk_words("a b c d e f g h", 3, 1) == ["a b c", "c d e", "e f g", "g h"]
assert chunk_words("a b c d e f g", 3, 1) == ["a b c", "c d e", "e f g"]   # ends exactly
assert chunk_words("a b c d e f", 2, 0) == ["a b", "c d", "e f"]           # no overlap
assert chunk_words("one two three four five", 3, 1) == ["one two three", "three four five"]   # real words
assert chunk_words("a b c d e", 5, 3) == ["a b c d e"]                     # two redundant tails
assert chunk_words("a b c d e f", 4, 2) == ["a b c d", "c d e f"]

# last short chunk
assert chunk_words("a b c d e", 3, 1) == ["a b c", "c d e"]                # no redundant "e"
assert chunk_words("a b c d", 3, 0) == ["a b c", "d"]                      # short tail is kept

# fewer words than size
assert chunk_words("hello world", 5, 2) == ["hello world"]

# empty text
assert chunk_words("", 3, 1) == []
assert chunk_words("   \n\t ", 3, 1) == []

# messy whitespace is normalised
assert chunk_words("a   b\n\nc  d", 2, 0) == ["a b", "c d"]

# invalid arguments must raise ValueError
bad_cases = [(3, 3), (3, 5), (0, 0), (-1, 0), (3, -1)]
failures = []

for bad_size, bad_overlap in bad_cases:
    try:
        chunk_words("a b c", bad_size, bad_overlap)
    except ValueError:
        pass                                   
    except Exception as e:
        failures.append(f"size={bad_size}, overlap={bad_overlap}: raised {type(e).__name__}, not ValueError")
    else:
        failures.append(f"size={bad_size}, overlap={bad_overlap}: no error raised")

assert not failures, "ValueError checks failed:\n" + "\n".join(failures)

print("all chunk_words tests passed")