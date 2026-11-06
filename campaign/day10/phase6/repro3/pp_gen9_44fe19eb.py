# area: context_managers
# hypothesis: An __exit__ annotated to return bool makes a name assigned after a raising statement possibly unbound after the block, while a None-returning __exit__ does not, and async with and suppress follow the same pattern.
# origin: llm
# hypothesis: an __exit__ annotated to return bool keeps a checker from proving the body finished, so a name assigned after a raising statement is possibly unbound, while an __exit__ returning None is not; async with and contextlib.suppress follow the same rules.
import asyncio
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from typing import reveal_type


class SwallowAsync:
    async def __aenter__(self) -> int:
        return 1

    async def __aexit__(self, *args: object) -> bool:
        return True


class PlainSync:
    def __enter__(self) -> str:
        return 'plain'

    def __exit__(self, *args: object) -> None:
        return None


@contextmanager
def tagged(tag: str) -> Iterator[str]:
    yield tag


def after_suppress(fail: bool) -> int:
    with suppress(ValueError):
        if fail:
            raise ValueError('bad')
        count = 5
    return count  # expect-error: count may be unbound


async def async_block(fail: bool) -> int:
    async with SwallowAsync() as level:
        reveal_type(level)
        if fail:
            raise KeyError('k')
        got = level + 1
    return got  # expect-error: got may be unbound


def strict_block(fail: bool) -> str:
    with PlainSync() as label:
        if fail:
            raise RuntimeError('strict')
        out = label.upper()
    return out


try:
    print(after_suppress(True))
except NameError as exc:
    print('suppress:', type(exc).__name__)
print(after_suppress(False))
try:
    print(asyncio.run(async_block(True)))
except NameError as exc:
    print('async:', type(exc).__name__)
print(asyncio.run(async_block(False)))
print(strict_block(False))
try:
    print(strict_block(True))
except RuntimeError as exc:
    print('strict:', type(exc).__name__)
with tagged('t') as t:
    reveal_type(t)
