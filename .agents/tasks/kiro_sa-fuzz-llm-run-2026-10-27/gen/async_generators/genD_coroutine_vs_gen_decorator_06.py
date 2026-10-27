import asyncio
from typing import Awaitable, Callable, Coroutine, Any, reveal_type


async def leaf(x: int) -> str:
    return str(x)


def wrap(f: Callable[[int], Awaitable[str]]) -> Callable[[int], Coroutine[Any, Any, str]]:
    async def inner(x: int) -> str:
        return (await f(x)) + "!"

    return inner


async def main() -> None:
    reveal_type(leaf)
    reveal_type(leaf(1))
    w = wrap(leaf)
    reveal_type(w)
    r = await w(2)
    reveal_type(r)
    t = asyncio.create_task(leaf(3))
    reveal_type(t)
    reveal_type(await t)
    rs = await asyncio.gather(leaf(1), asyncio.sleep(0, 5))
    reveal_type(rs)
    print(r, rs)


asyncio.run(main())
