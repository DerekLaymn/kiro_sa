import asyncio
from typing import AsyncIterator, Awaitable, reveal_type


async def nums(n: int) -> AsyncIterator[int]:
    for i in range(n):
        yield i


async def dbl(x: int) -> int:
    return x * 2


async def main() -> None:
    a = [await dbl(x) async for x in nums(3)]
    reveal_type(a)
    b = {x: await dbl(x) async for x in nums(3)}
    reveal_type(b)
    c = (x async for x in nums(2))
    reveal_type(c)
    d = [x async for x in nums(4) if await dbl(x) > 2]
    reveal_type(d)
    e = [dbl(x) for x in range(3)]
    reveal_type(e)
    f: list[Awaitable[int]] = e
    g = await asyncio.gather(*f)
    reveal_type(g)
    print(a, b, [x async for x in c], d, g)


asyncio.run(main())
