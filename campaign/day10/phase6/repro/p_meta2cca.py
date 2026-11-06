# area: constructors_metaclasses
# hypothesis: When a diamond of classes shares a metaclass whose __call__ is annotated to return int, the static type of Bottom(1) comes from that annotation rather than from the class or its __new__, and the runtime result is also an int.
# origin: runs/day10/parents/N_class/hv_constructors_metaclasses__conformance__constructors_call_metaclass.py
# area: constructors_metaclasses
# hypothesis: When a diamond of classes shares a metaclass whose __call__ is annotated to return int, the static type of Bottom(1) comes from that annotation rather than from the class or its __new__, and the runtime result is also an int.
from typing import Self, assert_type, reveal_type


class Meta(type):
    def __call__(cls, *args: int) -> int:
        return len(args)


class Base(metaclass=Meta):
    def __new__(cls, x: int) -> Self:
        return super().__new__(cls)


class Left(Base):
    pass


class Right(Base):
    pass


class Bottom(Left, Right):
    pass


b = Bottom(1)
reveal_type(b)
assert_type(b, int)
print(b, Left(2), Right(3), Base(4))
