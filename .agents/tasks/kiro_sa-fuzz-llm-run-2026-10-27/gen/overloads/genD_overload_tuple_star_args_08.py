from typing import overload, reveal_type


@overload
def pick(a: int) -> int: ...
@overload
def pick(a: int, b: str) -> str: ...
@overload
def pick(a: int, b: str, c: float) -> float: ...
def pick(a: int, b: str = "", c: float = 0.0) -> int | str | float:
    return a


def f(t1: tuple[int], t2: tuple[int, str], t3: tuple[int, ...], l: list[int]) -> None:
    reveal_type(pick(*t1))
    reveal_type(pick(*t2))
    reveal_type(pick(*t3))
    reveal_type(pick(*l))


f((1,), (1, "a"), (1,), [1])
print(pick(1), pick(1, "a"), pick(1, "a", 2.0))
