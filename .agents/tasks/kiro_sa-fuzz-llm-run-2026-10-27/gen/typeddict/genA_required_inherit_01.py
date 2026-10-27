from typing import reveal_type  # noqa

from typing import NotRequired, Required, TypedDict


class Base(TypedDict, total=False):
    a: int
    b: Required[str]


class Child(Base):
    c: NotRequired[float]
    d: bytes


def go(c: Child) -> None:
    reveal_type(c["b"])
    reveal_type(c["d"])
    reveal_type(c["a"])
    reveal_type(c.get("c"))
    reveal_type(c.get("a", 0))
    print(c)


go({"a": 1, "b": "x", "d": b""})
