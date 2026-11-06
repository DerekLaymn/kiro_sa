from typing import reveal_type


def g() -> str:
    return "x"


assert g() == 4
reveal_type(1)
