from typing import reveal_type


def g(x: int) -> str:
    return "s"


def pos() -> None:
    if g(3) == 4:
        reveal_type(g)
        reveal_type(g(1))


def neg() -> None:
    if g(3) == 4:
        pass
    else:
        reveal_type(g)
        reveal_type(g(1))


def after() -> None:
    if g(3) == 4:
        return
    reveal_type(g)
    reveal_type(g(1))
