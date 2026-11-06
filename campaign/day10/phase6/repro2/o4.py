from typing import reveal_type


def g(x: object) -> str:
    return "s"


def h() -> int:
    return 1


assert g(3) == "s"
reveal_type(g("a"))
assert h() == 4
reveal_type(h())
