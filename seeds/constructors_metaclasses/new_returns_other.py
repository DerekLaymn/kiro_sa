# area: constructors_metaclasses
# hypothesis: if __new__ returns a type that is not an instance of the class, __init__ is skipped and the
# call evaluates to __new__'s return type; metaclass __call__ can override construction.
# spec: typing spec, constructors.html.
from typing import Any, reveal_type


class Weird:
    def __new__(cls, x: int) -> int:  # not a Weird
        return x * 2

    def __init__(self, x: str) -> None:  # never called -> its signature must be ignored
        raise RuntimeError("unreachable")


class Meta(type):
    def __call__(cls, *args: Any, **kwargs: Any) -> str:
        return "made by metaclass"


class ViaMeta(metaclass=Meta):
    def __init__(self, x: int) -> None:
        pass


w = Weird(3)
reveal_type(w)  # int
v = ViaMeta()
reveal_type(v)  # str
print(w + 1, v.upper())
