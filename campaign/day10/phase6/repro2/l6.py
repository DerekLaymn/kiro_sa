from typing import Protocol


class Sink(Protocol):
    def __call__(self, value: int) -> None: ...


def call_by_keyword(sink: Sink) -> None:
    sink(value=1)


call_by_keyword(lambda x: print("x", x))
