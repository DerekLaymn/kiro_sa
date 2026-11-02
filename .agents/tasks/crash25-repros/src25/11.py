# area: async_generators
# origin: ruff mdtest with/async.md block 43
from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Protocol

class Stream[T](Protocol):
    def flatten(self: Stream[Stream[T]]) -> None: ...

@asynccontextmanager  # no diagnostic
async def open_stream(value: Stream[int]) -> AsyncGenerator[Stream[int], None]:
    yield value

reveal_type(open_stream)  # revealed: (value: Stream[int]) -> _AsyncGeneratorContextManager[Stream[int], None]
