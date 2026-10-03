# area: gradual_any
# hypothesis: Any is assignable both ways, object only upward; Any in a union/generic must not create
# errors that the fully-typed version doesn't have (gradual guarantee); explicit Any must not degrade to
# implicit Unknown (cf. astral-sh/ty#4536).
from typing import Any, reveal_type


def ident[T](x: T) -> T:
    return x


def first[T](xs: list[T]) -> T:
    return xs[0]


def take_int(x: int) -> int:
    return x


def f(a: Any, o: object, la: list[Any]) -> None:
    reveal_type(ident(a))  # Any
    reveal_type(first(la))  # Any
    reveal_type([a, 1])  # list[Any | int]
    take_int(a)  # ok
    take_int(o)  # expect-error
    n: int = a  # ok


f(1, 2, [3])
