from typing import Any, overload, reveal_type


@overload
def p(x: int) -> int: ...
@overload
def p(x: str) -> str: ...
def p(x: Any) -> Any:
    return x


@overload
def q(x: int, y: int) -> int: ...
@overload
def q(x: str, y: str) -> str: ...
def q(x: Any, y: Any) -> Any:
    return x + y


def f(a: Any, b: int, c: list[Any]) -> None:
    reveal_type(p(a))
    reveal_type(q(a, b))
    reveal_type(q(a, a))
    reveal_type(q(c[0], "s"))


f(1, 2, ["t"])
print(p(1), q("a", "b"))
