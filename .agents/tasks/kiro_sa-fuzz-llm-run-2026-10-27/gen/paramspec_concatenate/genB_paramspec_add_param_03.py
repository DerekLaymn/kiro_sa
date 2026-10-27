import sys
from collections.abc import Callable
from typing import Concatenate, reveal_type


def add_flag[**P, R](f: Callable[P, R]) -> Callable[Concatenate[bool, P], R]:
    def inner(flag: bool, /, *args: P.args, **kwargs: P.kwargs) -> R:
        return f(*args, **kwargs)

    return inner


@add_flag
def area(w: int, h: int = 2) -> int:
    return w * h


reveal_type(area)
print(area(True, 3), area(False, 3, h=4))
if len("") > 99:
    area(3)  # error: flag missing / bool expected (never executed)
