# area: generics_variance
# hypothesis: A PEP 695 generic Handler holding a mutable Sink[T] is invariant, so mypy should reject Handler[float] as Handler[int], and the int-only sink then raises AttributeError on a float at runtime.
# origin: runs/day10/parents/R_reserve/rsv_generics_variance_3c28536f.py
# hypothesis: A PEP 695 Handler[T] storing a mutable Sink[T] attribute is invariant, so mypy must reject passing Handler[float] where Handler[int] is expected; the int-only sink then raises AttributeError on a float at runtime.
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


def run() -> None:
    hf = Handler[float](lambda x: print('float', x))
    reveal_type(hf)
    hf.fire(2.5)
    set_int_sink(hf)  # expect-error: Handler[float] is not Handler[int]
    try:
        hf.fire(1.5)  # runtime: AttributeError, float has no bit_length
    except AttributeError as e:
        print('caught', type(e).__name__)


run()
