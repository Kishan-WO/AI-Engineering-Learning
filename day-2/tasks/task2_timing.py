from typing import Self
import asyncio
import functools
import inspect
import time
from collections.abc import Callable
from typing import Any

# **P (recommended) -> ParamSpec (old)
def timed[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Print how long func took, even if it raises. Works on sync and async functions."""
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                print(f"{func.__name__} took {time.perf_counter() - start:.3f}s")

        return async_wrapper  # type: ignore[return-value]

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            print(f"{func.__name__} took {time.perf_counter() - start:.3f}s")

    return wrapper


class timer:
    """Context manager that prints and records the time spent inside the block."""
    def __init__(self, label: str = "block") -> None:
        self.label = label
        self.elapsed = 0.0
        self._start = 0.0

    def __enter__(self) -> Self:
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.elapsed = time.perf_counter() - self._start
        print(f"{self.label} took {self.elapsed:.3f}s")
        # returning None lets any exception continue upward


### =============== TESTING ===============
if __name__ == "__main__":

    print("1. @timed keeps result and metadata")

    @timed
    def slow_add(a: int, b: int) -> int:
        """Add two numbers slowly."""
        time.sleep(0.05)
        return a + b

    result = slow_add(1, 2)
    print(f"   result   : {result}")
    print(f"   __name__ : {slow_add.__name__}")
    print(f"   __doc__  : {slow_add.__doc__}")
    assert result == 3
    assert slow_add.__name__ == "slow_add"
    assert slow_add.__doc__ == "Add two numbers slowly."
    print("   PASS\n")

    print("2. @timed prints the time and still raises")

    @timed
    def boom() -> None:
        raise ValueError("bad")

    try:
        boom()
    except ValueError as e:
        print(f"   caught   : ValueError({e})")
        assert str(e) == "bad"
    else:
        raise AssertionError("ValueError was swallowed")
    print("   PASS\n")

    print("3. @timed on an async function times the real run")

    @timed
    async def slow_async() -> str:
        await asyncio.sleep(0.1)
        return "done"

    print(f"   is coroutine function: {inspect.iscoroutinefunction(slow_async)}")
    assert inspect.iscoroutinefunction(slow_async)
    answer = asyncio.run(slow_async())
    print(f"   result   : {answer}")
    assert answer == "done"
    print("   PASS\n")

    print("4. timer() records at least the sleep time")
    with timer("sleep block") as t:
        time.sleep(0.1)
    print(f"   t.elapsed: {t.elapsed:.3f}s (expected 0.1 to 0.3)")
    assert 0.1 <= t.elapsed < 0.3, t.elapsed
    print("   PASS\n")

    print("5. timer() records the time and re-raises when the block fails")
    t2 = timer("failing block")  # created before the try, so it always exists in the except block
    try:
        with t2:
            raise RuntimeError("oops")
    except RuntimeError as e:
        print(f"   caught   : RuntimeError({e})")
        print(f"   t2.elapsed: {t2.elapsed:.6f}s")
        assert t2.elapsed > 0
    else:
        raise AssertionError("RuntimeError was swallowed")
    print("   PASS\n")

    print("all timing tests passed")
