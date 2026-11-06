# The Node.js Event Loop

Node.js runs JavaScript on a single thread and uses an event loop to handle I/O without blocking.

When an asynchronous operation finishes, its callback is placed in a queue. The event loop takes callbacks from the queue and runs them one at a time.

CPU-heavy work blocks the loop, so move it to worker threads. Python's asyncio uses the same idea.
