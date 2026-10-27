from collections.abc import Callable
from typing import Concatenate, reveal_type


def strip_first[**P, R](f: Callable[Concatenate[int, P], R]) -> Callable[P, R]:
    def inner(*a: P.args, **k: P.kwargs) -> R:
        return f(0, *a, **k)

    return inner


def h(x: int, y: str) -> str:
    return f"{x}{y}"


g = strip_first(h)
reveal_type(g)
print(g("a"))
print(g(y="b"))  # y is keyword-capable remainder
