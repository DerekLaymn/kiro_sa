# area: async_generators
# explores: contextlib.contextmanager / asynccontextmanager target types, suppress()
import asyncio
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager, suppress
from typing import reveal_type


@contextmanager
def opened(name: str) -> Iterator[list[str]]:
    lines = [name]
    try:
        yield lines
    finally:
        lines.clear()


@asynccontextmanager
async def session(user: str) -> AsyncIterator[dict[str, str]]:
    yield {"user": user}


async def main() -> str:
    async with session("ann") as s:
        reveal_type(s)  # dict[str, str]
        return s["user"]


with opened("a.txt") as lines:
    reveal_type(lines)  # list[str]
    lines.append("b")
    print(lines)
d: dict[str, int] = {}
with suppress(KeyError):
    d["missing"]
    print("never printed")
print(asyncio.run(main()))
with opened("x") as more:
    more.append(1)  # expect-error: list[str]
