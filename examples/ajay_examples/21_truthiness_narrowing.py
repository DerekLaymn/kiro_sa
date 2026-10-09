# area: narrowing_builtin
# explores: truthiness narrowing (if x / not x), `or`/`and` result types, __bool__ returning Literal[False]
from typing import Literal, reveal_type


def f(x: int | None, s: str, flag: Literal[0, 1, 2]) -> None:
    if x:
        reveal_type(x)  # int
    else:
        reveal_type(x)  # int | None
    y = x or 10
    reveal_type(y)  # int
    z = s and len(s)
    reveal_type(z)  # str | int
    if not flag:
        reveal_type(flag)  # Literal[0]
    else:
        reveal_type(flag)  # Literal[1, 2]


class AlwaysFalse:
    def __bool__(self) -> Literal[False]:
        return False


def g(v: AlwaysFalse | int) -> str:
    if v:
        reveal_type(v)  # int
        return "int"
    return "falsy"


f(0, "", 0)
f(5, "ab", 2)
print(g(AlwaysFalse()), g(3))
