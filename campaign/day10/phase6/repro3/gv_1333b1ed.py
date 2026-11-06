# area: generics_variance
# hypothesis: Because Handler[T] stores a mutable Sink[T] attribute, it is invariant, so mypy should reject a Handler[float | str] where Handler[int] is expected, and the int-only sink then raises AttributeError on a float at runtime.
# origin: runs/day10/parents/R_reserve/rsv_generics_variance_3c28536f.py
# area: generics_variance
# hypothesis: A PEP 695 Handler[T] with a mutable Sink[T] attribute is invariant, so mypy must reject a Handler[float | str] passed where Handler[int] is expected, and the int-only sink written through that alias fails at runtime.
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


hf = Handler[float | str](lambda x: print('float', x))
reveal_type(hf)
hf.fire(2.5)


def misuse() -> None:
    set_int_sink(hf)  # expect-error: Handler[float | str] is not Handler[int]


try:
    misuse()
    hf.fire(1.5)  # runtime: AttributeError, float has no bit_length
except AttributeError as e:
    print('caught', type(e).__name__)
