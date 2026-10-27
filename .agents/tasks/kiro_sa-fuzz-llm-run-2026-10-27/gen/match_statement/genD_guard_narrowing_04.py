from typing import assert_never, reveal_type


def f(x: int | str | None) -> str:
    match x:
        case int() if x > 0:
            reveal_type(x)
            return "pos"
        case int():
            reveal_type(x)
            return "nonpos"
        case str() as s if s:
            reveal_type(s)
            return "s"
        case str():
            return "empty"
        case None:
            return "none"
        case _:
            reveal_type(x)
            assert_never(x)


def g(x: int | str) -> str:
    match x:
        case int() | str() if isinstance(x, int):
            reveal_type(x)
            return "i"
        case _:
            reveal_type(x)
            return "o"


def h(x: tuple[int, int] | tuple[str]) -> int:
    match x:
        case (a, b) if a > b:
            reveal_type(x)
            return a
        case (a, _):
            return -a
        case (s,):
            reveal_type(s)
            return len(s)


print(f(1), f(-1), f("a"), f(""), f(None), g(1), g("a"), h((3, 1)), h((1, 2)), h(("ab",)))
