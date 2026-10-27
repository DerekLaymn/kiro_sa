from collections.abc import Callable
from typing import Concatenate, reveal_type


def drop_str[**P, R](f: Callable[Concatenate[str, P], R]) -> Callable[P, R]:
    def inner(*a: P.args, **k: P.kwargs) -> R:
        return f("d", *a, **k)

    return inner


def add_int[**P, R](f: Callable[P, R]) -> Callable[Concatenate[int, P], R]:
    def inner(n: int, /, *a: P.args, **k: P.kwargs) -> R:
        return f(*a, **k)

    return inner


@add_int
@drop_str
def fn(s: str, x: float) -> str:
    return s + str(x)


reveal_type(fn)
print(fn(1, 2.0))
print(fn(1, "no"))  # error
