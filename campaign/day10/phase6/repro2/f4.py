import enum


class F(enum.Flag):
    R = 1
    W = 2


def g(c: F) -> str:
    if c is F.R:
        return "R"
    elif c is F.W:
        return "W"
    return "x"
