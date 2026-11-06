from typing import reveal_type


def h() -> str:
    return "s"


def run() -> None:
    assert h() == 4
    reveal_type(h)
    reveal_type(h())
