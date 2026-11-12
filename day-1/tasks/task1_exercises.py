"""Day 1 exercises: strings, collections, comprehensions and match/case."""

from typing import Any
from collections import Counter, defaultdict

# 1. Strip the text and collapse any run of spaces, tabs or newlines into a single space.
def normalize_whitespace(text: str) -> str:
  """Strip text and collapse every run of whitespace into a single space.

  Example: "  hello \\n\\t  world  " -> "hello world"
  """
  print(" ".join(text.split()))

# normalize_whitespace("this is \n testing \t string.")
# print(normalize_whitespace("") == None)

# =======================

# 2. Check String is palindrome ( Ignore case and anything that isn't a letter or digit. )
def is_palindrome_v1(text: str) -> bool:
  """Return True if text reads the same backwards, ignoring case and non-alphanumerics.

  Uses filter() with str.isalnum to drop punctuation and spaces.
  """
  lower_text = "".join(filter(str.isalnum, text)).lower()
  return lower_text == lower_text[::-1]

def is_palindrome_v2(text: str) -> str:
  """Return True if text reads the same backwards, ignoring case and non-alphanumerics.

  Uses a generator expression instead of filter() (the more common style).
  """
  cleaned = "".join(ch.lower() for ch in text if ch.isalnum())
  return cleaned == cleaned[::-1]

# print(is_palindrome_v1("A man, a plan, a canal: Panama"))
# print(is_palindrome_v2("A man, a plan, a canal: Panama"))

# =======================

# 3. return first letter of word in capital and make short name D.K.S
def short_code(text: str) -> str:
  """Return uppercase initials joined with dots.

  Example: "ashish kumar patel" -> "A.K.P."
  """
  return "".join(f"{word[0].upper()}." for word in text.split())

# print(short_code("AB CD DFGH"))

# =======================

# 4. mask phone number
def mask_phone(text: str) -> str:
  """Keep only the digits, then mask all but the last 4 with '*'.

  Example: "+91 98765-43210" -> "********3210"
  """
  return f"{'*'*(len(text)-4)}{text[-4:]}"

# print(mask_phone("+91 9192939495"))
# print(mask_phone("1234"))

# =======================

# 5. Return (number_of_characters, number_of_utf8_bytes)
def utf8_report(text: str) -> tuple[int, int]:
  """Return (number of characters, number of UTF-8 bytes) for text.

  Example: "नमस्ते" -> (6, 18), since each Devanagari character takes 3 bytes.
  """
  encoded_text = text.encode('utf-8')
  return (len(text), len(encoded_text))

# print(utf8_report("Hello! 👋"))
# print(utf8_report("नमस्ते"))

# =======================

# 6. Count words case-insensitively and return the top_n most common. Break ties alphabetically.
def word_frequencies(text: str, top_n: int) -> list[tuple[str, int]]:
  """Return the top_n most common words as (word, count) pairs.

  Counting is case-insensitive; ties are broken alphabetically.
  Example: ("the cat the dog The end", 2) -> [("the", 3), ("cat", 1)]
  """
  word_counts = Counter(text.split())
  res = [(key, word_counts.get(key)) for key in word_counts]
  return res[:top_n]

# print(word_frequencies("the cat the dog The end", 2))

# =======================

# 7. Remove duplicates but keep the order in which items first appear.
def dedupe_keep_order(items: list) -> list:
  """Return items with duplicates removed, keeping first-appearance order.

  Uses a set for O(1) membership checks while building the result list.
  """
  my_set = set()
  res = []
  for item in items:
    if item not in my_set:
      my_set.add(item)
      res.append(item)
  return res

# print(dedupe_keep_order([4, 1, 2, 1, 3]))

# =======================

# 8. Group people's names by city, skipping people with no city.
def group_by_city(people: list[dict[str, str]]) -> dict[str, list[str]]:
    """Group people's names by city, skipping people with no "city" key.

    Returns a plain dict (not a defaultdict) so later missing-key lookups raise.
    """
    groups: defaultdict[str, list[str]] = defaultdict(list)
    for person in people:
        if "city" in person:
            groups[person["city"]].append(person["name"])
    return dict(groups)

people = [
    {"name": "Asha", "city": "Pune"},
    {"name": "Ravi", "city": "Delhi"},
    {"name": "Meera", "city": "Pune"},
    {"name": "Kabir"},
]
# print(group_by_city(people))

# =======================

# 9. Return a new dict where keys in overrides win, and leave both inputs unchanged.
def merge_settings_v1(defaults: dict, overrides: dict) -> dict:
    """Return a new dict of defaults updated with overrides, using the | operator.

    Shallow merge: nested dicts are replaced, not merged.
    """
    return defaults | overrides

def merge_settings_v2(defaults: dict, overrides: dict) -> dict:
    """Return a new dict of defaults updated with overrides, using ** unpacking.

    Equivalent to JavaScript's {...defaults, ...overrides}; also a shallow merge.
    """
    return {**defaults, **overrides}

d = {"model": "small", "temperature": 0.0}
o = {"temperature": 0.7}
# print(merge_settings_v1(d, o))

# =======================

# 10. Rotate the list right by k, where k can be larger than the list's length.
def rotate(items: list, k: int) -> list:
    """Return a new list rotated right by k positions.

    k may exceed len(items); an empty list returns [] (avoids k % 0).
    """
    if not items:
        return []
    k %= len(items)
    return items[-k:] + items[:-k]

# print(rotate([1, 2, 3, 4, 5], 2))

# =======================

# 11
def squares_of_evens(nums: list[int]) -> list[int]:
  """Return the squares of the even numbers in nums, in order."""
  return [num**2 for num in nums if num % 2 == 0]

# print(squares_of_evens([1, 2, 3, 4, 5, 6]))

# =======================

# 12 Build a map from each value to the keys that had it. Use a dict comprehension if you can, and explain in a comment why that's awkward here.
# i.e invert_dict({"a": 1, "b": 2, "c": 1}) == {1: ["a", "c"], 2: ["b"]}
def invert_dict(d: dict[str, int]) -> dict[int, list[str]]:
  """Map each value to the list of keys that had it (first attempt).

  Superseded by the recommended version below.
  """
  res = {}
  for [key, value] in d.items():
    if res.get(value) == None:
      res[value] = [key]
    else:
      res.get(value).append(key)
  return res

# Recommended
def invert_dict(d: dict[str, int]) -> dict[int, list[str]]:
    """Map each value to the list of keys that had it.

    Example: {"a": 1, "b": 2, "c": 1} -> {1: ["a", "c"], 2: ["b"]}
    """
    res: dict[int, list[str]] = {}
    for key, value in d.items():
        if value not in res:
            res[value] = []
        res[value].append(key)
    return res

# print(invert_dict({"a": 1, "b": 2, "c": 1}))

# =======================

# 13. Flatten a 2-D list and keep only the values >= min_value
def flatten_and_filter(matrix: list[list[int]], min_value: int) -> list[int]:
  """Flatten a 2-D list and keep only values >= min_value, in row order."""
  return [item for row in matrix for item in row if item >= min_value]

# print(flatten_and_filter([[1, 5], [7, 2], [9]], 5))

# =======================

# 14. Describe point using x and y position in tuple
def describe_point(point: tuple):
  """Describe where a 2-D point lies (first attempt; prints instead of returning).

  Superseded by the recommended version below.
  """
  match point:
    case [x, 0]:
      print(f"point on X axis at {x}")
    case [0, y]:
      print(f"point on Y axis at {y}")
    case [x, y]:
      print(f"point at ({x}, {y})")
    case _:
      print("point is not in 2D")

# recommended version
def describe_point(point: tuple[int, ...]) -> str:
    """Describe where a 2-D point lies.

    Returns "origin", "on x-axis at X", "on y-axis at Y", "point at (X, Y)",
    or "not a 2-D point" for any other shape.
    """
    match point:
        case (0, 0):
            return "origin"
        case (0, y):
            return f"on y-axis at {y}"
        case (x, 0):
            return f"on x-axis at {x}"
        case (x, y):
            return f"point at ({x}, {y})"
        case _:
            return "not a 2-D point"

# [x, 0] and (x, 0) mean the same thing in a pattern, and both match lists and tuples.

# describe_point((0, 1))
# describe_point((7, 0))
# describe_point((7, 5))

# =======================

# 15. Handle different type of event and display its message
def handle_event(event: dict[str, str]):
  """Route an event dict to a message (first attempt; prints instead of returning).

  Superseded by the recommended version below.
  """
  # v1
  # try:
  #   event_type = event["type"]
  # except KeyError:
  #   print("unknown event")
  #   return

  # v2
  event_type = event.get("type")

  match event_type:
    case "message":
      role, content = event["role"], event["content"]
      print(f"{role} said: {content}")
    case "tool_call":
      print(f"calling {event.get("name")} with {event.get("args")}")
    case "error":
      code = event["code"]
      if code == 429:
        print("rate limited")
      elif code == 500:
        print("error 500")
    case _:
      print("unknown event")

'''
Bugs in Above
#1 Bug: any error code except 429 and 500 returns nothing
#2 Bug: it crashes on a message with missing fields i.e missing role
'''

# Recommended version
def handle_event(event: dict[str, Any]) -> str:
    """Route an event dict to a human-readable description.

    Uses dict patterns, so a missing key makes that case not match
    instead of raising KeyError.
    """
    match event:
        case {"type": "message", "role": role, "content": content}:
            return f"{role} said: {content}"
        case {"type": "tool_call", "name": name, "args": args}:
            return f"calling {name} with {args}"
        case {"type": "error", "code": 429}:
            return "rate limited, retry later"
        case {"type": "error", "code": code}:
            return f"error {code}"
        case _:
            return "unknown event"

# handle_event({"type": "message", "role": "user", "content": "hi"})
# handle_event({"type": "message", "role": "assistant", "content": "hello"})
# handle_event({"type": "tool_call", "name": "search", "args": {"q": "python"}})
# handle_event({"type": "error", "code": 429})
# handle_event({"type": "error", "code": 500})
# handle_event({"foo": "bar"})
# handle_event({"type": "unknown"})