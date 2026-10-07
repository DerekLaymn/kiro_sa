# area: narrowing_builtin
# explores: NoReturn calls end control flow; narrowing continues after them; Never in exhausted branches
from typing import NoReturn, reveal_type


def fail(msg: str) -> NoReturn:
    raise RuntimeError(msg)


def parse(x: int | str | None) -> int:
    if x is None:
        fail("missing")
    reveal_type(x)  # int | str
    if isinstance(x, str):
        return int(x)
    return x


def must_be(x: int | str) -> int:
    if isinstance(x, int):
        return x
    if isinstance(x, str):
        return len(x)
    reveal_type(x)  # Never
    fail("unreachable")


print(parse(3), parse("4"), must_be("ab"))
try:
    parse(None)
except RuntimeError as exc:
    print("runtime:", exc)
