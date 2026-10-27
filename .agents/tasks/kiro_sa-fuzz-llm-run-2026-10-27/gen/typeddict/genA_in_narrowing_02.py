from typing import reveal_type  # noqa

from typing import Literal, NotRequired, TypedDict


class A(TypedDict):
    kind: Literal["a"]
    x: int


class B(TypedDict):
    kind: Literal["b"]
    y: str
    z: NotRequired[int]


def go(v: A | B) -> None:
    if v["kind"] == "a":
        reveal_type(v)
    else:
        reveal_type(v)
    if "z" in v:
        reveal_type(v)
        reveal_type(v["z"])
    if "x" in v:
        reveal_type(v)


go({"kind": "a", "x": 1})
go({"kind": "b", "y": "s", "z": 1})
