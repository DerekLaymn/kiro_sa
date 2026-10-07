# area: descriptors_properties
# explores: __slots__ restricts instance attributes; slot attributes are descriptors on the class
from typing import reveal_type


class Point:
    __slots__ = ("x", "y")

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


class Point3(Point):
    __slots__ = ("z",)

    def __init__(self, x: int, y: int, z: int) -> None:
        super().__init__(x, y)
        self.z = z


p = Point3(1, 2, 3)
reveal_type(p.x)  # int
reveal_type(p.z)  # int
print(p.x, p.y, p.z)
try:
    p.w = 4  # expect-error: w is not in __slots__
except AttributeError as exc:
    print("runtime:", exc)
