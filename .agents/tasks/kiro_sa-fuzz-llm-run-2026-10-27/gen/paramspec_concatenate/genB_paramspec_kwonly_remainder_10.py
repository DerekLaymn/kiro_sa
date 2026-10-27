import sys
from collections.abc import Callable
from typing import Concatenate, reveal_type


def pre[**P, R](f: Callable[Concatenate[int, P], R]) -> Callable[P, R]:
    def inner(*a: P.args, **k: P.kwargs) -> R:
        return f(1, *a, **k)

    return inner


@pre
def fn(a: int, *, key: str) -> str:
    return f"{a}{key}"


reveal_type(fn)
print(fn(key="k"))
if len("") > 99:
    fn("k")  # error: keyword-only (never executed)
