# Python Dictionaries

A dictionary maps keys to values. Lookups, inserts and deletes are O(1) on average because dictionaries are hash tables.

Keys must be hashable, so strings, numbers and tuples work, but lists do not. Since Python 3.7, dictionaries keep insertion order.

Useful helpers include `dict.get(key, default)`, `setdefault`, and `collections.defaultdict`, which creates a default value the first time a missing key is used.
