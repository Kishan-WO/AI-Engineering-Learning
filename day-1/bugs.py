"""Day 1, task 4: reproduce the mutable-default bug and a shallow-copy bug, then fix both.

Run from the day-1 folder:  python bugs.py
Every section prints what happens, and the asserts prove the bug and the fix.
"""

import copy
from typing import Any

# =====================================================================
# Bug 1: the mutable default argument
# =====================================================================
#
# A default value is evaluated ONCE, when `def` runs, not on every call.
# So a list used as a default is a single list object shared by every
# call that doesn't pass its own. In JavaScript, `function f(x = [])`
# creates a new array on each call, so this surprises JS developers.

def add_tag_buggy(tag: str, tags: list[str] = []) -> list[str]:  # noqa: B006 (the bug on purpose)
    """Append tag to tags and return it (buggy: the default list is shared)."""
    tags.append(tag)
    return tags


def add_tag_fixed(tag: str, tags: list[str] | None = None) -> list[str]:
    """Append tag to tags and return it, creating a new list when none is given."""
    if tags is None:  # the None pattern: create the list inside the function
        tags = []
    tags.append(tag)
    return tags


def demo_mutable_default() -> None:
    print("=== Bug 1: mutable default argument ===")

    first = add_tag_buggy("python")
    second = add_tag_buggy("fastapi")
    print(f"buggy  first call : {first}")
    print(f"buggy  second call: {second}")
    print(f"buggy  same object? {first is second}  (id {id(first)} vs {id(second)})")
    defaults_tuple: tuple[Any, ...] = add_tag_buggy.__defaults__ or ()  # __defaults__ is None for a function with no defaults
    print(f"buggy  the default itself now holds: {defaults_tuple[0]}")

    # The bug: the second call "remembers" the first call's tag,
    # and both results are literally the same list.
    assert second == ["python", "fastapi"]
    assert first is second

    first = add_tag_fixed("python")
    second = add_tag_fixed("fastapi")
    print(f"fixed  first call : {first}")
    print(f"fixed  second call: {second}")
    print(f"fixed  same object? {first is second}")

    assert first == ["python"]
    assert second == ["fastapi"]
    assert first is not second

    # Passing your own list still works as expected.
    mine = ["day1"]
    assert add_tag_fixed("python", mine) is mine
    assert mine == ["day1", "python"]

    # This is exactly why docstore's Document uses
    #     tags: list[str] = field(default_factory=list)
    # default_factory calls list() for every new Document. A plain
    # `tags: list[str] = []` is refused by @dataclass with a ValueError,
    # because it would cause this very bug.
    print()


# =====================================================================
# Bug 2: the shallow copy
# =====================================================================
#
# dict.copy(), {**d}, d | {}, list(x) and x[:] are all SHALLOW: they make
# a new outer container, but the values inside are the same objects.
# Changing a nested list or dict through the copy changes the original.
# JavaScript's {...obj} and [...arr] behave the same way.

DEFAULT_SETTINGS: dict[str, Any] = {  # mixed values (str, dict, list), so the values are Any
    "model": "small",
    "llm": {"temperature": 0.0, "max_tokens": 500},
    "stop_words": ["the", "a"],
}


def demo_shallow_copy() -> None:
    print("=== Bug 2: shallow copy ===")

    # --- The bug ---
    defaults = copy.deepcopy(DEFAULT_SETTINGS)  # a private copy so the demo can be re-run safely
    user = defaults.copy()                       # shallow copy

    user["model"] = "large"                     # top level: replaced in the copy only
    user["llm"]["temperature"] = 0.9             # nested: same dict as defaults["llm"]
    user["stop_words"].append("an")              # nested: same list as defaults["stop_words"]

    print(f"shallow  outer dict same?  {user is defaults}")
    print(f"shallow  nested dict same? {user['llm'] is defaults['llm']}")
    print(f"shallow  defaults after editing the copy: {defaults}")

    assert defaults["model"] == "small"              # top-level change did NOT leak
    assert defaults["llm"]["temperature"] == 0.9     # nested change DID leak: the bug
    assert defaults["stop_words"] == ["the", "a", "an"]

    # Merging (exercise 9) is shallow too: the merged result shares nested objects.
    base = copy.deepcopy(DEFAULT_SETTINGS)
    merged: dict[str, Any] = base | {"model": "large"}
    merged["llm"]["max_tokens"] = 9999
    print(f"merge    base['llm'] after editing merged: {base['llm']}")
    assert base["llm"]["max_tokens"] == 9999

    # --- The fix ---
    defaults = copy.deepcopy(DEFAULT_SETTINGS)
    user = copy.deepcopy(defaults)                # copies every nested level

    user["llm"]["temperature"] = 0.9
    user["stop_words"].append("an")

    print(f"deep     nested dict same? {user['llm'] is defaults['llm']}")
    print(f"deep     defaults after editing the copy: {defaults}")

    assert defaults["llm"]["temperature"] == 0.0
    assert defaults["stop_words"] == ["the", "a"]
    assert user["llm"] is not defaults["llm"]

    # The same trap with lists of lists: [[0] * 3] * 3 repeats ONE inner list.
    grid = [[0] * 3] * 3
    grid[0][0] = 1
    print(f"grid     [[0]*3]*3 after grid[0][0] = 1: {grid}")
    assert grid == [[1, 0, 0], [1, 0, 0], [1, 0, 0]]

    grid = [[0] * 3 for _ in range(3)]            # fix: a new inner list per row
    grid[0][0] = 1
    print(f"grid     comprehension version:        {grid}")
    assert grid == [[1, 0, 0], [0, 0, 0], [0, 0, 0]]
    print()


if __name__ == "__main__":
    demo_mutable_default()
    demo_shallow_copy()
    print("all bug demos behaved as expected")
