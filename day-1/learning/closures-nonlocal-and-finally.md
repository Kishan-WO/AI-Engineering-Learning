# Closures, `nonlocal` and `try/finally`

Where I met it, in the middleware:
```python
status_code = 500

async def send_with_headers(message):
    nonlocal status_code
    if message["type"] == "http.response.start":
        status_code = message["status"]
    ...

try:
    await self.app(scope, receive, send_with_headers)
finally:
    ...log the request...
```

## 1. Closures
A **closure** is an inner function that **remembers the variables of the function around it**, even after the outer function has returned. Same idea as JavaScript.

```python
def make_counter():
    count = 0
    def inc():
        nonlocal count
        count += 1
        return count
    return inc

inc = make_counter()
inc(); inc()
inc()        # 3
```
`count` lives on, hidden inside `inc`. Nobody else can touch it.

## 2. Why `nonlocal`
Python decides where a variable lives by **where it is assigned**. An assignment inside a function creates a **new local variable**:

```python
def no_nonlocal():
    status = 500
    def set_it():
        status = 200      # creates a NEW local variable, outer one untouched
    set_it()
    return status

no_nonlocal()   # 500
```
To change the outer variable, the inner function must say so:

```python
nonlocal status
status = 200      # now the outer variable is changed
```
| Keyword | Refers to |
|---|---|
| (nothing) | read-only access to outer variables works; assignment makes a new local |
| `nonlocal x` | the variable `x` in the nearest enclosing function |
| `global x` | the module-level variable `x` |

(Reading an outer variable needs no keyword. Only **assigning** does.)

JavaScript comparison: in JS an inner function assigns to the outer `let` directly; Python needs `nonlocal`.

## 3. Why the middleware needs both
`send_with_headers` is the function the app calls to send the response. The middleware needs to know the **status code** later, in the log line. The inner function runs while the response is being sent, so it:
- uses `nonlocal status_code` to store the real status in the outer variable, and
- the outer function reads `status_code` in its `finally` block.

No class and no global variable: the closure carries the value.

## 4. `try / finally`
`finally` runs **no matter how the `try` block ends**: normally, by `return`, or by an error.

```python
def f():
    try:
        return "returned"
    finally:
        print("finally ran")
# prints "finally ran" first, then f() returns "returned"

def g():
    try:
        raise ValueError("boom")
    finally:
        print("finally ran before the error moved on")
# the error still propagates after finally
```
- `finally` does **not** stop an exception. The exception continues after it.
- Use it for cleanup that must always happen: closing files, releasing connections, logging.

In the middleware, the `finally` writes the log line whether the request succeeded or crashed. If the app raised, the status stays 500 (the starting value) and the error moves on to the error handler.

## Common mistakes
| Mistake | What happens |
|---|---|
| Assigning to an outer variable without `nonlocal` | A new local is created; the outer value is unchanged |
| Using `nonlocal` for a module-level variable | `SyntaxError`; use `global` |
| Using `nonlocal` for a name that doesn't exist outside | `SyntaxError: no binding for nonlocal` |
| Returning inside `finally` | It swallows any pending exception; avoid it |
| Thinking `finally` catches errors | It only runs; use `except` to handle |

## Quick check
- What is a closure?
- Why does `status = 200` inside an inner function not change the outer `status`?
- What does `nonlocal` fix?
- Does `finally` run after a `return`? After an exception?
- Why does the middleware use `finally` for its log line?
