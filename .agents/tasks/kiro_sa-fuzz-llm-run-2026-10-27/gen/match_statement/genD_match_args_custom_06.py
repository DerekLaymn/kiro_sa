from typing import reveal_type


class Pt:
    __match_args__ = ("y", "x")

    def __init__(self, x: int, y: str) -> None:
        self.x = x
        self.y = y


class Sub(Pt):
    pass


def f(o: Pt | int) -> str:
    match o:
        case Sub(a, b):
            reveal_type(a)
            reveal_type(b)
            return "sub"
        case Pt(a, b):
            reveal_type(a)
            reveal_type(b)
            return a + str(b)
        case Pt(x=1):
            reveal_type(o)
            return "unreachable"
        case _:
            reveal_type(o)
            return "o"


print(f(Pt(1, "a")), f(Sub(2, "b")), f(5))
