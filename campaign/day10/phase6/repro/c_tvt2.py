from collections.abc import Callable
from typing import reveal_type


class Foo[*Ts, **P = [float, bool]]:
    def __init__(self, fn: Callable[P, tuple[*Ts]]) -> None:
        self.fn = fn


def one(a: float, b: bool) -> tuple[int]:
    return (1,)


foo = Foo[int](one)
reveal_type(foo)
