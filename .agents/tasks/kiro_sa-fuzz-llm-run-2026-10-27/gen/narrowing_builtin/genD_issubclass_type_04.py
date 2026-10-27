from typing import reveal_type


class Base: ...
class Left(Base): ...
class Right(Base): ...


def f(t: type[Left] | type[Right] | type[int]) -> str:
    if issubclass(t, Base):
        reveal_type(t)
        return t.__name__
    reveal_type(t)
    return "other"


def g(t: type[Base]) -> str:
    if issubclass(t, (Left, Right)):
        reveal_type(t)
        return "lr"
    reveal_type(t)
    return "base"


def h(t: type) -> str:
    if issubclass(t, int):
        reveal_type(t)
        return "int"
    return "x"


print(f(Left), f(int), g(Left), g(Base), h(bool), h(str))
