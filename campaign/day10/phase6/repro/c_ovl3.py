from typing import reveal_type


def f(x: str, y: int) -> None:
    assert x == y
    reveal_type(1)


def h(x: str) -> None:
    assert x == 4
    reveal_type(2)
