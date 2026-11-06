# Python Lists

A list is an ordered, mutable collection. You create one with square brackets: `nums = [1, 2, 3]`.

## Common operations
- `append(x)` adds an item to the end in O(1) time.
- `insert(0, x)` adds to the front but costs O(n), because every item shifts.
- Slicing with `nums[1:3]` returns a new list.

## When to use a list
Use a list when order matters and you mostly add to the end. If you need fast removal from the front, use `collections.deque` instead.
