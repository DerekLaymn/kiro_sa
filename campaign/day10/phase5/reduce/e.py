from abc import ABC, abstractmethod
from typing import reveal_type


class Shape(ABC):
    @abstractmethod
    def area(self, scale: int) -> int: ...


class Square(Shape):
    def __init__(self, side: int) -> None:
        self.side = side

    def area(self, scale: int) -> int:
        return self.side * self.side * scale


assert issubclass(Square, Shape)
reveal_type(Square)
sq = Square(2)
reveal_type(sq)
reveal_type(sq.area(3))
