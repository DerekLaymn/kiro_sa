from typing import reveal_type  # noqa

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class Box(Generic[T]):
    item: T
    extras: list[T]


@dataclass
class IntBox(Box[int]):
    label: str = ""


def go() -> None:
    b = Box("s", ["t"])
    reveal_type(b)
    ib = IntBox(1, [2], "l")
    reveal_type(ib.item)
    reveal_type(ib.extras)
    bad = Box(1, ["x"])
    print(b, ib, bad)


go()
