from typing import reveal_type


def g(x: object) -> str:
    return "s"


def run() -> None:
    assert g(3) == 4
    reveal_type(g("a"))
    reveal_type(1)
