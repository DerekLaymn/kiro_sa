from typing import reveal_type


def f(t: tuple[int, str, float] | tuple[int] | tuple[()]) -> int:
    match t:
        case ():
            reveal_type(t)
            return 0
        case (a,):
            reveal_type(t)
            reveal_type(a)
            return a
        case (a, *rest):
            reveal_type(t)
            reveal_type(rest)
            return a + len(rest)


def g(xs: list[int] | str | bytes) -> int:
    match xs:
        case [a, b, *_]:
            reveal_type(xs)
            reveal_type(a)
            return a + b
        case [*_]:
            reveal_type(xs)
            return 1
        case _:
            reveal_type(xs)
            return 2


def h(t: tuple[int, ...]) -> int:
    match t:
        case (a, *mid, z):
            reveal_type(mid)
            return a + z + len(mid)
        case _:
            reveal_type(t)
            return 0


print(f(()), f((1,)), f((1, "a", 2.0)), g([1, 2, 3]), g([1]), g("ab"), h((1, 2, 3)), h((1,)))
