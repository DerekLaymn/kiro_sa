# area: generics_variance
# hypothesis: A PEP 695 Handler[T] with a mutable Sink[T] attribute is invariant, so checkers must reject a Handler[float] where a Handler[int] is expected, and the int-only sink written through that alias raises AttributeError on a float at runtime.
# origin: runs/day10/parents/R_reserve/rsv_generics_variance_3c28536f.py
# area: generics_variance
# hypothesis: A PEP 695 Handler[T] with a mutable Sink[T] attribute is invariant, so checkers must reject a Handler[float] where Handler[int] is expected even though int is a subtype of float, and the int-only sink then fails on a float at runtime.
from typing import Protocol, reveal_type


class Sink[T](Protocol):
    def __call__(self, value: T) -> None: ...


class Handler[T]:
    def __init__(self, sink: Sink[T]) -> None:
        self.sink: Sink[T] = sink

    def fire(self, value: T) -> None:
        self.sink(value)


def set_int_sink(h: Handler[int]) -> None:
    h.sink = lambda x: print('bits', x.bit_length())


hi = Handler[int](lambda x: print('int', x))
hi.fire(2)
hf = Handler[float](lambda x: print('float', x))
reveal_type(hf)
hf.fire(2.5)
hf.fire(3)


def misuse() -> None:
    set_int_sink(hf)  # expect-error: Handler[float] is not Handler[int]


try:
    misuse()
    hf.fire(1.5)  # runtime: AttributeError, float has no bit_length
except AttributeError as e:
    print('caught', type(e).__name__)
