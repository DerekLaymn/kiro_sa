from typing import Protocol


class Sink(Protocol):
    def __call__(self, value: int) -> None: ...


def named_value(value: int) -> None: ...
def named_x(x: int) -> None: ...
def named_positional(x: int, /) -> None: ...


a: Sink = lambda x: None
b: Sink = lambda value: None
c: Sink = named_value
d: Sink = named_x
e: Sink = named_positional
