from collections.abc import Callable
from typing import Protocol


class Sink(Protocol):
    def __call__(self, value: int, /) -> None: ...


def use(s: Sink) -> None: ...
def use_c(s: Callable[[int], None]) -> None: ...


use(lambda x: None)
use_c(lambda x: None)
