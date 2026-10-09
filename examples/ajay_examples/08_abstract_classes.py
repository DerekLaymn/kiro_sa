# area: abstract_classes
# explores: abstract methods and abstract properties; instantiating abstract classes; type[Abstract]
from abc import ABC, abstractmethod
from typing import reveal_type


class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    def describe(self) -> str:
        return f"{self.name}: {self.area()}"


class Unit(Shape):
    def area(self) -> float:
        return 1.0

    @property
    def name(self) -> str:
        return "unit"


class Half(Shape):  # forgets the abstract property `name`
    def area(self) -> float:
        return 0.5


def build(cls: type[Shape]) -> Shape:
    return cls()  # allowed: cls may be a concrete subclass


reveal_type(Unit().name)  # str
reveal_type(build(Unit))  # Shape
print(Unit().describe(), build(Unit).area())
for make in (Shape, Half):
    try:
        make()  # expect-error (for both): cannot instantiate abstract class
    except TypeError as exc:
        print("runtime:", exc)
try:
    build(Shape)  # mypy: only a concrete class can be given (type-abstract)
except TypeError as exc:
    print("runtime:", exc)
