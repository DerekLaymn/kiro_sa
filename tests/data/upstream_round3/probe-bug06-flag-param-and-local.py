import enum
from typing import reveal_type


class F(enum.Flag):
    R = 1
    W = 2


def h(x: F) -> str:
    if x is F.R:
        return "R"
    elif x is F.W:
        return "W"
    else:
        reveal_type(x)
        return 1 + "bad"


def k() -> str:
    b = F.R | F.W
    reveal_type(b)
    if b is F.R:
        return "R"
    elif b is F.W:
        return "W"
    else:
        reveal_type(b)
        return 1 + "bad"


print(h(F.R | F.W))
print(k())
