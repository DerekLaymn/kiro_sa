# area: async_generators
# hypothesis: ty aborts with a stack overflow on a PEP 695 protocol whose method takes `self: Stream[Stream[T]]`, used through @asynccontextmanager. Vary: drop the decorator, make the protocol covariant, use a plain generic class, nest Stream three deep.
# origin: harvested program seed-50a85e2bdd8d (ruff mdtest with/async.md block 43; live ty crash, no upstream entry matched)
from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Protocol

class Stream[T](Protocol):
    def flatten(self: Stream[Stream[T]]) -> None: ...

@asynccontextmanager  # ok
async def open_stream(value: Stream[int]) -> AsyncGenerator[Stream[int], None]:
    yield value

reveal_type(open_stream)  # revealed: (value: Stream[int]) -> _AsyncGeneratorContextManager[Stream[int], None]
