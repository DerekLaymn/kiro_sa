from typing import Literal, TypeVar, overload, reveal_type

T = TypeVar("T")


@overload
def norm(x: Literal["a", "b"]) -> Literal["A", "B"]: ...
@overload
def norm(x: str) -> str: ...
@overload
def norm(x: T) -> T: ...
def norm(x: object) -> object:
    return x


def run(v: Literal["a", "b"] | int) -> None:
    reveal_type(norm(v))
