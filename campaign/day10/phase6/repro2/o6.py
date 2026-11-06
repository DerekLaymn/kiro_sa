from typing import reveal_type


def g(x: object) -> str:
    return "s"


assert g(3) == 4
print("after")
reveal_type(g("a") + "x")
reveal_type(len(g("a")))
