# Bug 1 (ty): see examples/bugs/README.md for the issue link and the expected/actual result.
from typing import Protocol


class Stream[T](Protocol):
    def flatten(self: "Stream[Stream[T]]") -> None: ...


class Impl:
    def flatten(self) -> None: ...


x: Stream[int] = Impl()
