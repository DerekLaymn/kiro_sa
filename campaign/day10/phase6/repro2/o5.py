from typing import reveal_type


def g(x: object) -> str:
    return "s"


v = g(3)
assert v == 4
reveal_type(v)
reveal_type(g("a"))
