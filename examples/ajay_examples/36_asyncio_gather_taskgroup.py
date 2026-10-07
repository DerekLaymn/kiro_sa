# area: async_generators
# explores: asyncio.gather tuple inference, gather(*list), TaskGroup tasks, wait_for, awaiting a non-awaitable
import asyncio
from typing import reveal_type


async def fetch_int(n: int) -> int:
    await asyncio.sleep(0)
    return n


async def fetch_str(s: str) -> str:
    await asyncio.sleep(0)
    return s


def not_async() -> int:
    return 1


async def main() -> None:
    a, b = await asyncio.gather(fetch_int(1), fetch_str("x"))
    reveal_type(a)  # int
    reveal_type(b)  # str
    results = await asyncio.gather(*[fetch_int(i) for i in range(3)])
    reveal_type(results)  # list[int]
    async with asyncio.TaskGroup() as tg:
        t = tg.create_task(fetch_str("y"))
    reveal_type(t)  # Task[str]
    reveal_type(t.result())  # str
    done = await asyncio.wait_for(fetch_int(5), timeout=1)
    reveal_type(done)  # int
    print(a, b, results, t.result(), done)
    try:
        await not_async()  # expect-error: int is not awaitable
    except TypeError as exc:
        print("runtime:", exc)


asyncio.run(main())
