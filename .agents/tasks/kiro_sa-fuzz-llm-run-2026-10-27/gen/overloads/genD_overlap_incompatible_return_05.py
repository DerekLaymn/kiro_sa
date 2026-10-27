from typing import overload, reveal_type


@overload
def f(x: int) -> int: ...
@overload
def f(x: bool) -> str: ...
def f(x: int) -> int | str:
    return "b" if isinstance(x, bool) else x


@overload
def g(x: object) -> int: ...
@overload
def g(x: str) -> str: ...
def g(x: object) -> int | str:
    return x if isinstance(x, str) else 0


def use(b: bool, s: str) -> None:
    reveal_type(f(b))
    reveal_type(f(3))
    reveal_type(g(s))
    reveal_type(g(b))


use(True, "s")
print(f(True), f(2), g("a"), g(1))
