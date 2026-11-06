import enum
from typing import reveal_type


class F(enum.Flag):
    R = 1
    W = 2


def f(c: F) -> str:
    if c == F.R:
        return "R"
    reveal_type(c)
    return "not R"


def g(c: F) -> str:
    if c is F.R:
        return "R"
    elif c is F.W:
        return "W"
    else:
        reveal_type(c)
        return "other"


print(f(F.R | F.W), g(F.R | F.W))
