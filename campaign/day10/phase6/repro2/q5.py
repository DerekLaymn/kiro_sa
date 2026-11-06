from typing import reveal_type


def g(x: int) -> int:
    return 1


def sz(x: object) -> int:
    return 1


def run() -> None:
    assert g(3) == 4
    reveal_type(g)
    assert sz(3) == 2
    reveal_type(sz)
    assert str(3) == 4
    reveal_type(str)
    reveal_type(int)
