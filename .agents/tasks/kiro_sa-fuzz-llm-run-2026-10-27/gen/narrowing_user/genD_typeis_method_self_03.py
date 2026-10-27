from typing import Any, TypeIs, TypeGuard, reveal_type


class Shape:
    def is_circle(self, other: object) -> TypeIs["Circle"]:
        return isinstance(other, Circle)

    @staticmethod
    def is_sq(other: object) -> TypeGuard["Square"]:
        return isinstance(other, Square)

    @classmethod
    def is_cls(cls, other: object) -> TypeIs["Shape"]:
        return isinstance(other, cls)


class Circle(Shape): ...
class Square(Shape): ...


def f(x: Circle | Square | int, s: Shape) -> None:
    if s.is_circle(x):
        reveal_type(x)
    else:
        reveal_type(x)
    if Shape.is_sq(x):
        reveal_type(x)
    else:
        reveal_type(x)
    if Shape.is_cls(x):
        reveal_type(x)
    else:
        reveal_type(x)


def g(x: Any) -> None:
    if Shape().is_circle(x):
        reveal_type(x)


f(Circle(), Shape())
f(3, Shape())
g(Circle())
