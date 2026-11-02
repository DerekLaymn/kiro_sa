from typing import TypedDict


class T(TypedDict):
    a: int


def g(t: T) -> None:
    reveal_type(t["b"])
