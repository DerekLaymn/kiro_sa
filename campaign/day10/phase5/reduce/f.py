# area: overloads
# hypothesis: With the object overload listed first, the int overload of describe is unreachable and checkers should flag it, while describe(3) still returns 4 at runtime.
# origin: runs/day10/parents/O_overload/hv_overloads__conformance__overloads_definitions.py
# Hypothesis: with the object overload listed before the int overload, the int overload
# is unreachable and checkers should report it, while the runtime still dispatches int
# arguments through the implementation.
from abc import ABC, abstractmethod
from typing import overload, reveal_type, assert_type


@overload
def describe(x: object) -> str: ...
@overload
def describe(x: int) -> int: ...
def describe(x: object) -> object:
    return 'obj:' + str(x) if not isinstance(x, int) else x + 1


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


reveal_type(describe(3))
assert_type(describe('a'), str)
assert describe('a') == 'obj:a'
assert issubclass(Square, Shape)
sq = Square(2)
reveal_type(sq.area(3))
assert sq.area(3) == 12
assert sq.area(0.5) == 2.0
