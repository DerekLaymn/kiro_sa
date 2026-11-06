# area: abstract_classes
# hypothesis: Instantiating a subclass that leaves an abstract property unimplemented must be rejected statically and raises TypeError at runtime, while ABC.register only adds an isinstance relation and does not enforce abstract members.
# origin: llm
# area: abstract_classes
# hypothesis: Instantiating a subclass that leaves an abstract property unimplemented must be rejected statically and raises TypeError at runtime, while ABC.register only adds an isinstance relation and does not enforce abstract members.
from abc import ABC, abstractmethod
from typing import reveal_type


class Shape(ABC):
    @property
    @abstractmethod
    def area(self) -> float: ...

    @abstractmethod
    def scale(self, k: float) -> Shape: ...


class Square(Shape):
    def __init__(self, side: float) -> None:
        self.side = side

    @property
    def area(self) -> float:
        return self.side * self.side

    def scale(self, k: float) -> Shape:
        return Square(self.side * k)


class Lazy(Shape):
    def scale(self, k: float) -> Shape:
        return self


class Named:
    def __init__(self, label: str) -> None:
        self.label = label


Shape.register(Named)


def probe_lazy() -> str:
    try:
        obj = Lazy()  # expect-error: Lazy leaves abstract property area unimplemented
        reveal_type(obj)
    except TypeError:
        return 'TypeError'
    return 'built'


sq = Square(3.0)
reveal_type(sq.area)
print(sq.scale(2.0).area)
print(isinstance(Named('x'), Shape))
print(probe_lazy())
