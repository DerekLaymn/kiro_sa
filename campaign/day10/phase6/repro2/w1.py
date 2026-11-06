import asyncio
from contextlib import AsyncExitStack


class SwallowAsync:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *args: object) -> bool:
        return True


async def get(fail: bool) -> int:
    async with SwallowAsync():
        if fail:
            raise KeyError("k")
        value = 1
    return value


print(asyncio.run(get(False)))
try:
    print(asyncio.run(get(True)))
except NameError as exc:
    print(type(exc).__name__)
