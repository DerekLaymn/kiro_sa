# area: context_managers
# hypothesis: For an async with block whose __aexit__ returns bool and returns False, the ValueError propagates to the enclosing try, and ExitStack callbacks run last-in first-out.
# origin: llm
# area: context_managers
# hypothesis: For an async with block whose __aexit__ returns bool and returns False, the ValueError propagates to the enclosing try, and ExitStack callbacks run last-in first-out.
import asyncio
from contextlib import ExitStack
from typing import reveal_type


class Guard:
    async def __aenter__(self) -> int:
        return 7

    async def __aexit__(self, *args: object) -> bool:
        return False


def lifo(log: list[str]) -> list[str]:
    with ExitStack() as stack:
        stack.callback(log.append, 'first')
        stack.callback(log.append, 'second')
    return log


async def use_guard() -> str:
    x: int | None = None
    try:
        async with Guard() as value:
            x = value
            raise ValueError('boom')
    except ValueError:
        return f'propagated {x}'
    reveal_type(x)
    return 'swallowed'


print(lifo([]))
print(asyncio.run(use_guard()))
