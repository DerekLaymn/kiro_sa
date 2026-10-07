# area: narrowing_builtin
# explores: hasattr() and callable() narrowing
from collections.abc import Callable
from typing import reveal_type


class Duck:
    def quack(self) -> str:
        return "quack"


class Robot:
    pass


class Named:
    name = "n"


def speak(x: Duck | Robot) -> str:
    if hasattr(x, "quack"):
        reveal_type(x)  # Duck | (Robot & <has quack>)
        return x.quack()
    reveal_type(x)  # Robot
    return "beep"


def maybe_call(v: int | Callable[[], int]) -> int:
    if callable(v):
        reveal_type(v)  # () -> int
        return v()
    reveal_type(v)  # int
    return v


def attr_or_default(o: object) -> str:
    if hasattr(o, "name"):
        reveal_type(o.name)
        return str(o.name)
    return "?"


print(speak(Duck()), speak(Robot()), maybe_call(3), maybe_call(lambda: 4), attr_or_default(Named()), attr_or_default(1))
