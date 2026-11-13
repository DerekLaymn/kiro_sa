# Bug 11 (mypy): see examples/bugs/README.md for the issue link and the expected/actual result.
from typing import Protocol


class Sink(Protocol):
    def __call__(self, value: int) -> None: ...


def call_by_keyword(sink: Sink) -> None:
    sink(value=1)


def named_x(x: int) -> None: ...


def with_def() -> None:
    call_by_keyword(named_x)  # mypy: error


s1: Sink = lambda x, /: None  # mypy: no error
s2: Sink = lambda y, z=0: None  # mypy: no error
call_by_keyword(lambda x: None)  # mypy: no error
