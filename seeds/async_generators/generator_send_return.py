# area: async_generators
# hypothesis: Generator send/return types flow through `yield from`, and async iterators/awaitables
# compose correctly.
# spec: typing spec doesn't cover all of this; CPython + typeshed are the reference.
import asyncio
from collections.abc import AsyncIterator, Generator
from typing import reveal_type


def inner() -> Generator[int, str, bool]:
    s = yield 1
    reveal_type(s)  # str
    return s == "stop"


def outer() -> Generator[int, str, None]:
    done = yield from inner()
    reveal_type(done)  # bool
    yield 2


async def ticks(n: int) -> AsyncIterator[int]:
    for i in range(n):
        await asyncio.sleep(0)
        yield i


async def main() -> list[int]:
    out = [i async for i in ticks(3)]
    reveal_type(out)  # list[int]
    return out


g = outer()
print(next(g), g.send("go"))
print(asyncio.run(main()))
g2 = outer()
next(g2)
g2.send(5)  # expect-error: send type is str (runtime: inner compares 5 == "stop" -> fine, so no crash)
