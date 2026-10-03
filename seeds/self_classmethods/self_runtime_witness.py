# area: self_classmethods
# hypothesis: an unsound acceptance of a `Self` parameter leads to a runtime AttributeError
# (gives typediff a RUNTIME oracle, not just a spec argument).
from typing import Self


class Shape:
    def same_kind(self, other: Self) -> bool:
        return type(self) is type(other)

    def combine(self, other: Self) -> Self:
        return other


class Circle(Shape):
    def radius(self) -> float:
        return 1.0


c = Circle().combine(Shape())  # expect-error: Shape is not a Circle
print(c.radius())  # AttributeError at runtime if the call above was wrongly accepted
