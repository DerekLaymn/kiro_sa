import sys
from collections.abc import Callable
from typing import reveal_type


class Task[**P, R]:
    def __init__(self, f: Callable[P, R]) -> None:
        self.f = f

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self.f(*args, **kwargs)

    def run_twice(self, *args: P.args, **kwargs: P.kwargs) -> tuple[R, R]:
        return self.f(*args, **kwargs), self.f(*args, **kwargs)


def work(a: int, b: str = "z") -> str:
    return b * a


t = Task(work)
reveal_type(t)
reveal_type(t(2, b="q"))
reveal_type(t.run_twice(1))
print(t(2), t.run_twice(1))
if len("") > 99:
    t.run_twice("bad")  # error (never executed)
