# area: self_classmethods
# hypothesis: the inherited-`Self`-parameter bug may also affect classmethods, properties and nested types.
# spec: PEP 673 - `Self` in a classmethod binds to the class it is called on.
from typing import Self, reveal_type


class Base:
    @classmethod
    def merge(cls, a: Self, b: Self) -> Self:
        return a

    @property
    def me(self) -> Self:
        return self

    def pair(self, other: tuple[Self, int]) -> Self:
        return other[0]


class Child(Base):
    pass


reveal_type(Child.merge)
reveal_type(Child().me)
Child.merge(Child(), Base())  # expect-error: Base is not a Child
Child().pair((Base(), 1))  # expect-error: tuple[Base, int] is not tuple[Child, int]
print("done")
