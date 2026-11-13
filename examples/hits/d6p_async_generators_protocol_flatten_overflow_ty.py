# area: async_generators
# hypothesis: A covariant protocol with a Stream[Stream[T_co]] self annotation, consumed by an async generator, should type-check, but ty overflows its stack.
# origin: runs/hits/d3p_crash_ty_stack_overflow_protocol_flatten.py
# hypothesis: a covariant generic protocol whose method takes self: Stream[Stream[T]], used through an async generator; ty overflows its stack resolving the protocol.
import asyncio
from collections.abc import AsyncGenerator
from typing import Protocol, TypeVar

T_co = TypeVar('T_co', covariant=True)


class Stream(Protocol[T_co]):
    def flatten(self: 'Stream[Stream[T_co]]') -> None: ...


class Impl:
    def flatten(self) -> None:
        print('flatten')


async def open_stream(value: Stream[int]) -> AsyncGenerator[Stream[int], None]:
    yield value


async def main() -> None:
    async for s in open_stream(Impl()):
        print(type(s).__name__)


Impl().flatten()
asyncio.run(main())
