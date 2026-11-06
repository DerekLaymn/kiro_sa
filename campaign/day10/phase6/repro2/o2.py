from typing import reveal_type


def g(x: object) -> str:
    return "s"


assert g(3) == 4
reveal_type(g("a"))
reveal_type(g)
reveal_type(g(3))
