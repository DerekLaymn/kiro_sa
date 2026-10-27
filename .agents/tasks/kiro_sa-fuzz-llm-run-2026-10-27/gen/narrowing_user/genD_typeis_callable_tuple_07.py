from typing import Callable, TypeIs, reveal_type


def is_pair(x: object) -> TypeIs[tuple[int, int]]:
    return isinstance(x, tuple) and len(x) == 2


def is_cb(x: object) -> TypeIs[Callable[[int], int]]:
    return callable(x)


def f(x: tuple[int, int] | tuple[int, int, int] | int) -> None:
    if is_pair(x):
        reveal_type(x)
    else:
        reveal_type(x)


def g(x: int | Callable[[int], int] | Callable[[str], str]) -> int:
    if is_cb(x):
        reveal_type(x)
        return 1
    reveal_type(x)
    return 0


f((1, 2))
f(3)
print(g(1), g(lambda n: n))
