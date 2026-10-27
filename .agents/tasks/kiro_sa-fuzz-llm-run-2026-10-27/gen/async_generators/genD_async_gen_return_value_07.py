import asyncio
from typing import AsyncGenerator, AsyncIterable, reveal_type


async def src() -> AsyncGenerator[int, None]:
    yield 1
    yield 2


async def relay(s: AsyncIterable[int]) -> AsyncGenerator[str, None]:
    async for x in s:
        yield str(x)


async def bad() -> AsyncGenerator[int, None]:
    yield "x"  # wrong yield type


async def main() -> None:
    r = relay(src())
    reveal_type(r)
    reveal_type(await anext(r))
    reveal_type(await anext(r, None))
    reveal_type(aiter(r))
    print([x async for x in r])
    print([x async for x in bad()])


asyncio.run(main())
