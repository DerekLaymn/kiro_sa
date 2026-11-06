from typing import reveal_type


def g(x: int) -> str:
    return "s"


def run() -> None:
    assert g(3) == "a" or g(3) == 4
    reveal_type(g)
    assert g(4) in (4, 5)
    reveal_type(g)
