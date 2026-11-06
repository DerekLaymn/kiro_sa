from abc import ABC, abstractmethod
from typing import overload, reveal_type


class Shape(ABC):
    @overload
    @abstractmethod
    def area(self, scale: int) -> int: ...
    @overload
    @abstractmethod
    def area(self, scale: float) -> float: ...


class Square(Shape):
    def __init__(self, side: int) -> None:
        self.side = side

    @overload
    def area(self, scale: int) -> int: ...
    @overload
    def area(self, scale: float) -> float: ...
    def area(self, scale: int | float) -> int | float:
        return self.side * self.side * scale


sq = Square(2)
reveal_type(sq.area(3))
