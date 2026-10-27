import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, reveal_type


@asynccontextmanager
async def res(name: str) -> AsyncIterator[list[str]]:
    buf = [name]
    try:
        yield buf
    finally:
        buf.append("closed")


@asynccontextmanager
async def two() -> AsyncIterator[tuple[int, str]]:
    yield (1, "a")


async def main() -> None:
    reveal_type(res)
    reveal_type(res("x"))
    async with res("x") as b, two() as (n, s):
        reveal_type(b)
        reveal_type(n)
        reveal_type(s)
        print(b, n, s)


asyncio.run(main())
