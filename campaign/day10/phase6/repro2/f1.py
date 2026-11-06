import enum
from typing import reveal_type


class F(enum.Flag):
    R = 1
    W = 2


def f(c: F) -> None:
    if c == F.R:
        return
    reveal_type(c)


def g(c: F) -> None:
    if c is F.R:
        return
    reveal_type(c)


def h(c: F) -> None:
    if c is F.R or c is F.W:
        return
    reveal_type(c)


f(F.R | F.W)
g(F.R | F.W)
h(F.R | F.W)
