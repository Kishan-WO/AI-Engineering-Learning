# Python Decorators

A decorator is a function that takes a function and returns a new function. The `@retry` or `@timed` syntax is shorthand for `func = retry(func)`.

Decorators are useful for logging, timing, caching and retries. Always use `functools.wraps` inside a decorator so the wrapped function keeps its name and docstring.

A decorator that takes arguments, such as `@retry(times=3)`, needs one more layer: a function that returns the decorator.
