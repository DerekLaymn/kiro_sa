# area: generics_variance
# explores: classmethods on generic classes (Box.of, Box[str].of), classmethods on a specialized subclass,
# generic staticmethods
from typing import Self, reveal_type


class Box[T]:
    def __init__(self, item: T) -> None:
        self.item = item

    @classmethod
    def of(cls, item: T) -> "Box[T]":
        return cls(item)

    @classmethod
    def copy_of(cls, other: Self) -> Self:
        return cls(other.item)

    @staticmethod
    def pair[U](a: U, b: U) -> "tuple[Box[U], Box[U]]":
        return Box(a), Box(b)


class IntBox(Box[int]):
    pass


reveal_type(Box.of(1))  # Box[int]
reveal_type(Box[str].of("s"))  # Box[str]
reveal_type(IntBox.of(3))  # Box[int]
reveal_type(IntBox.copy_of(IntBox(1)))  # IntBox
reveal_type(Box.pair(1, "a"))  # tuple[Box[int | str], Box[int | str]]
print(Box.of(1).item, IntBox.copy_of(IntBox(1)).item, Box.pair(1, 2)[1].item)
Box[str].of(1)  # expect-error: int is not str
IntBox.of("x")  # expect-error: str is not int
