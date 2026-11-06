import enum
from typing import reveal_type


class E(enum.Enum):
    R = 1
    W = 2


def f(c: E) -> None:
    if c == E.R:
        return
    reveal_type(c)


def g(c: E) -> None:
    if c is E.R:
        return
    reveal_type(c)
