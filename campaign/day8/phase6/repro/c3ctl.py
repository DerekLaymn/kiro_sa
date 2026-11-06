from typing import Literal, overload, reveal_type


@overload
def norm(x: Literal["a", "b"]) -> Literal["A", "B"]: ...
@overload
def norm(x: int) -> int: ...
def norm(x: object) -> object:
    return x


def run(v: Literal["a", "b"] | int) -> None:
    reveal_type(norm(v))
