import sys
from collections.abc import Callable
from typing import Concatenate, reveal_type


def logged[S, **P, R](f: Callable[Concatenate[S, P], R]) -> Callable[Concatenate[S, P], R]:
    def inner(self: S, *args: P.args, **kwargs: P.kwargs) -> R:
        return f(self, *args, **kwargs)

    return inner


class Acc:
    def __init__(self) -> None:
        self.total = 0

    @logged
    def add(self, n: int, *, scale: int = 1) -> int:
        self.total += n * scale
        return self.total


a = Acc()
reveal_type(a.add)
print(a.add(2, scale=3))
if len("") > 99:
    a.add("x")  # error (never executed)
