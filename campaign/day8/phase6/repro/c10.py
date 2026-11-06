from typing import Any, Literal, overload, reveal_type


@overload
def f(x: Literal["a"]) -> Literal["A"]: ...
@overload
def f(x: int) -> int: ...
def f(x: Any) -> Any:
    return x


def g(a: Any) -> None:
    reveal_type(f(a))
