# area: protocols
# hypothesis: Assigning a plain class to a Stream[Stream[T]] self-annotated protocol should type-check, while ty overflows its stack; the runtime isinstance check returns True.
# origin: runs/hits/d4v_protocols_expanding_self_receiver.py
# hypothesis: a plain class assigned to a protocol whose method annotates self as Stream[Stream[T]] overflows ty's stack; CPython runs the runtime-checkable isinstance check normally.
from typing import Protocol, runtime_checkable


@runtime_checkable
class Stream[T](Protocol):
    def flatten(self: 'Stream[Stream[T]]') -> None: ...


class Impl:
    def flatten(self) -> None:
        print('flatten')


x: Stream[int] = Impl()
print(isinstance(x, Stream), type(x).__name__)
Impl().flatten()
