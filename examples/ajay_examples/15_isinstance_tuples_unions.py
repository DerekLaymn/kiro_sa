# area: narrowing_builtin
# explores: isinstance with a tuple of classes and with a `X | Y` union object; issubclass on type[...]
from typing import reveal_type


def f(x: int | str | bytes | None) -> str:
    if isinstance(x, (int, str)):
        reveal_type(x)  # int | str
        return str(x)
    reveal_type(x)  # bytes | None
    if isinstance(x, bytes | None):
        reveal_type(x)  # bytes | None
    return "other"


def g(t: type[int] | type[str]) -> str:
    if issubclass(t, int):
        reveal_type(t)  # type[int]
        return "int"
    reveal_type(t)  # type[str]
    return "str"


def h(x: object) -> int:
    if isinstance(x, list) and all(isinstance(i, int) for i in x):
        reveal_type(x)  # list[Unknown] / list[Any] (all() does not narrow elements)
        return len(x)
    return 0


print(f(1), f(b"x"), f(None), g(bool), g(str), h([1, 2]))
