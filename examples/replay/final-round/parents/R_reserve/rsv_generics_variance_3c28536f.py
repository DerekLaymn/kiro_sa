# area: generics_variance
# hypothesis: A PEP 695 generic Handler that stores a mutable Protocol __call__ taking T is invariant, so mypy should reject Handler[float] for Handler[int], and the int-only sink then fails on a float at runtime.
# origin: earlier generated parent (not kept)
# area: generics_variance
# hypothesis: A PEP 695 Handler[T] with a mutable Sink[T] attribute is invariant, so mypy must reject Handler[float] where Handler[int] is expected, and the int-only sink written through that alias fails at runtime.
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


hf = Handler[float](lambda x: print('float', x))
reveal_type(hf)
hf.fire(2.5)


def misuse() -> None:
    set_int_sink(hf)  # expect-error: Handler[float] is not Handler[int]


try:
    misuse()
    hf.fire(1.5)  # runtime: AttributeError, float has no bit_length
except AttributeError as e:
    print('caught', type(e).__name__)
