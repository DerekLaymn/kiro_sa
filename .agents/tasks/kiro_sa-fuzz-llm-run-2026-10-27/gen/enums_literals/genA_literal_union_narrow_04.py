from typing import reveal_type  # noqa

from typing import Literal, assert_never

Op = Literal["add", "sub", "mul"]


def apply(op: Op, a: int, b: int) -> int:
    if op == "add":
        return a + b
    elif op == "sub":
        return a - b
    elif op == "mul":
        return a * b
    reveal_type(op)
    assert_never(op)


def pick(flag: bool, n: Literal[1, 2, 3]) -> Literal[1, 2, 3, "x"]:
    if n in (1, 2):
        reveal_type(n)
        return n
    return "x" if flag else n


def go(s: str) -> None:
    if s in ("add", "sub"):
        reveal_type(s)
    x: Literal["add", "sub"] = "add"
    y: Op = x
    reveal_type(y)
    print(apply(y, 1, 2), pick(True, 2), s)


go("add")
