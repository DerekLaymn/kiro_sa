from typing import TypeGuard, TypeIs, reveal_type


def guard_int(x: object) -> TypeGuard[int]:
    return isinstance(x, int)


def is_int(x: object) -> TypeIs[int]:
    return isinstance(x, int)


def f(x: int | str) -> None:
    if guard_int(x):
        reveal_type(x)
    else:
        reveal_type(x)
    if is_int(x):
        reveal_type(x)
    else:
        reveal_type(x)


def g(x: bool | str) -> None:
    if is_int(x):
        reveal_type(x)
    else:
        reveal_type(x)


f(1)
f("a")
g(True)
g("s")
