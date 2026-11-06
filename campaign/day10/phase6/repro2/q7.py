from typing import reveal_type


def g(x: int) -> str:
    return "s"


def run(y: int) -> None:
    assert g(y) == 4
    reveal_type(y)
    reveal_type(g)
