import asyncio
from typing import AsyncGenerator, AsyncIterator, reveal_type


async def agen() -> AsyncGenerator[int, str]:
    got = yield 1
    reveal_type(got)
    got2 = yield len(got)
    reveal_type(got2)


async def as_iter() -> AsyncIterator[str]:
    yield "a"
    yield "b"


async def main() -> None:
    g = agen()
    reveal_type(g)
    a = await g.asend(None)  # type: ignore[arg-type]
    reveal_type(a)
    b = await g.asend("hello")
    reveal_type(b)
    out = [x async for x in as_iter()]
    reveal_type(out)
    print(a, b, out)
    await g.aclose()


asyncio.run(main())
