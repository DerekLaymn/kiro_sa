import enum
from typing import Literal, assert_never, reveal_type


class C(enum.Enum):
    R = 1
    G = 2
    B = 3


def f(c: C) -> str:
    match c:
        case C.R:
            return "r"
        case C.G | C.B:
            reveal_type(c)
            return "gb"
        case _:
            reveal_type(c)
            assert_never(c)


def g(x: Literal[1, 2] | None | bool) -> str:
    match x:
        case 1:
            reveal_type(x)
            return "one"
        case 2:
            return "two"
        case None:
            return "n"
        case False:
            return "f"
        case _:
            reveal_type(x)
            assert_never(x)


print(f(C.R), f(C.B), g(1), g(None), g(False))
print(g(True))
