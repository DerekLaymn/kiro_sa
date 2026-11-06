from typing import reveal_type


def name(n: int) -> str:
    return str(n)


def run(n: int) -> None:
    assert name(n) == 4
    reveal_type(n)


def run_x(n: int) -> None:
    if name(n) == 4:
        reveal_type(n)
    reveal_type(n)


def run_y(n: int) -> None:
    x = name(n) == 4
    reveal_type(x)
    if x:
        reveal_type(n)
