import asyncio
import functools
import inspect
import random
import time
from collections.abc import Callable
from typing import Any


def backoff_delay(attempt: int, base_delay: float, max_delay: float) -> float:
    """The longest wait after failed attempt number `attempt` (0 for the first failure).

    The delay doubles each time and is capped at max_delay.
    """
    return min(max_delay, base_delay * 2**attempt)


def compute_delay(attempt: int, base_delay: float, max_delay: float) -> float:
    """Seconds to actually wait: a random value between 0 and the backoff delay ("full jitter"),
    so many clients do not retry at the same moment.
    """
    return random.uniform(0, backoff_delay(attempt, base_delay, max_delay))


def retry[**P, R](
    times: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
    exceptions: tuple[type[BaseException], ...] = (ConnectionError, TimeoutError),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Retry a sync or async function when it raises one of `exceptions`.

    times      total number of attempts (3 means 1 try + 2 retries)
    base_delay delay after the first failure; it doubles after each failure
    max_delay  upper limit for a single delay
    exceptions only these exception types are retried; anything else is raised at once

    Each wait is a random value between 0 and the backoff delay (jitter).

    After the last attempt the last exception is re-raised.
    """
    if times < 1:
        raise ValueError(f"times must be at least 1, got {times}")

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                for attempt in range(times):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions:
                        if attempt == times - 1:
                            raise
                        delay = compute_delay(attempt, base_delay, max_delay)
                        await asyncio.sleep(delay)  # never time.sleep here: it would block the loop

            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == times - 1:
                        raise
                    delay = compute_delay(attempt, base_delay, max_delay)
                    time.sleep(delay)
            raise AssertionError("unreachable: the loop always returns or raises")

        return wrapper

    return decorator


### =============== TESTING ===============

if __name__ == "__main__":

    def flaky(fail_times: int, error: type[BaseException] = ConnectionError):
        """Build a function that fails `fail_times` times, then returns 'ok'. Counts its calls."""
        state = {"calls": 0}

        def func() -> str:
            """Flaky docstring."""
            state["calls"] += 1
            if state["calls"] <= fail_times:
                raise error(f"fail #{state['calls']}")
            return "ok"

        return func, state

    print("1. success on the first try -> called once")
    func, state = flaky(0)
    assert retry(times=3, base_delay=0.01)(func)() == "ok"
    print(f"   calls: {state['calls']}")
    assert state["calls"] == 1
    print("   PASS\n")

    print("2. fails twice, then succeeds -> 3 calls")
    func, state = flaky(2)
    assert retry(times=3, base_delay=0.01)(func)() == "ok"
    print(f"   calls: {state['calls']}")
    assert state["calls"] == 3
    print("   PASS\n")

    print("3. always fails -> the last exception after `times` calls")
    func, state = flaky(99)
    try:
        retry(times=3, base_delay=0.01)(func)()
    except ConnectionError as e:
        print(f"   raised: ConnectionError({e}) after {state['calls']} calls")
        assert str(e) == "fail #3"
    else:
        raise AssertionError("expected ConnectionError")
    assert state["calls"] == 3
    print("   PASS\n")

    print("4. exception not in `exceptions` -> raised at once, 1 call")
    func, state = flaky(99, error=ValueError)
    try:
        retry(times=3, base_delay=0.01)(func)()
    except ValueError:
        print(f"   raised: ValueError after {state['calls']} call")
    else:
        raise AssertionError("expected ValueError")
    assert state["calls"] == 1
    print("   PASS\n")

    print("5. backoff delays double and respect max_delay")
    assert [backoff_delay(a, 0.5, 8.0) for a in range(6)] == [0.5, 1.0, 2.0, 4.0, 8.0, 8.0]
    delays = [backoff_delay(a, 0.01, 0.03) for a in range(4)]
    print(f"   delays with base 0.01 and cap 0.03: {delays}")
    assert delays == [0.01, 0.02, 0.03, 0.03]
    print("   PASS\n")

    print("6. jitter keeps every delay between 0 and the cap")
    samples = [compute_delay(3, 0.5, 8.0) for _ in range(1000)]
    print(f"   1000 samples: min {min(samples):.2f}, max {max(samples):.2f} (cap is 4.00)")
    assert all(0 <= s <= 4.0 for s in samples)
    assert len(set(samples)) > 900
    print("   PASS\n")

    print("7. name and docstring are kept")
    func, _ = flaky(0)
    wrapped = retry()(func)
    print(f"   __name__: {wrapped.__name__}, __doc__: {wrapped.__doc__}")
    assert wrapped.__name__ == "func" and wrapped.__doc__ == "Flaky docstring."
    print("   PASS\n")

    print("8. times < 1 is rejected")
    try:
        retry(times=0)
    except ValueError as e:
        print(f"   ValueError: {e}")
    else:
        raise AssertionError("expected ValueError")
    print("   PASS\n")

    print("9. async version: retries, and does not block the loop")

    def make_async_flaky(fail_times: int):
        state = {"calls": 0}

        @retry(times=3, base_delay=0.05)
        async def func() -> str:
            state["calls"] += 1
            if state["calls"] <= fail_times:
                raise TimeoutError("slow")
            return "ok"

        return func, state

    async def run_async() -> None:
        (f1, s1), (f2, s2) = make_async_flaky(1), make_async_flaky(1)
        assert inspect.iscoroutinefunction(f1)
        start = time.perf_counter()
        results = await asyncio.gather(f1(), f2())
        elapsed = time.perf_counter() - start
        print(f"   results: {results}, calls: {s1['calls']} and {s2['calls']}, total {elapsed:.2f}s")
        assert results == ["ok", "ok"] and s1["calls"] == s2["calls"] == 2
        assert elapsed < 0.09, "the two waits should overlap (about 0.05s), not add up (0.10s)"

    asyncio.run(run_async())
    print("   PASS\n")

    print("all retry tests passed")
