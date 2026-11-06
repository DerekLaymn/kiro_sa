import enum
from typing import reveal_type


class I(enum.IntFlag):
    A = 1
    B = 2


def f(c: I) -> str:
    if c == I.A:
        return "A"
    reveal_type(c)
    return "not A"


print(f(I.A | I.B))
