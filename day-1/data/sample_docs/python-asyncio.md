# Python asyncio

asyncio lets one thread handle many I/O-bound tasks at once. A coroutine is defined with `async def` and paused with `await`.

## The event loop
The event loop runs coroutines and switches between them whenever one is waiting on I/O. This is similar to the Node.js event loop.

## A common mistake
Calling `time.sleep()` inside a coroutine blocks the whole loop. Use `await asyncio.sleep()` instead. Use `asyncio.gather` to run several coroutines concurrently.
