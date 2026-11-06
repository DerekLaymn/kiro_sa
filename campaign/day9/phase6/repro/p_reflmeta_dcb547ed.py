# area: constructors_metaclasses
# hypothesis: CPython dispatches A * B on class objects to RightMeta.__rmul__ first because RightMeta subclasses LeftMeta and overrides the reflected method, and an annotation-only __len__ is visible to checkers but raises TypeError at runtime.
# origin: runs/day9/parents/D_shadow/d4v_metaclass_reflected_op.py
# area: constructors_metaclasses
# hypothesis: CPython dispatches A * B on class objects to RightMeta.__rmul__ first because RightMeta subclasses LeftMeta and overrides the reflected method, and an annotation-only __len__ is visible to checkers but raises TypeError at runtime.
from collections.abc import Callable
from typing import assert_type, reveal_type


class LeftMeta(type):
    def __mul__(cls, other: object) -> int:
        return 1


class RightMeta(LeftMeta):
    def __rmul__(cls, other: object) -> str:
        return "s"


class A(metaclass=LeftMeta):
    pass


class B(metaclass=RightMeta):
    pass


def reflected() -> str:
    reveal_type(A * B)
    assert_type(A * B, str)
    return A * B


class Sized:
    __len__: Callable[[], int]

    def __init__(self) -> None:
        self.size = 3


class Counted:
    def __len__(self) -> int:
        return 5


def probe_len(s: Sized) -> str:
    try:
        n = len(s)  # expect-error
    except TypeError:
        return "TypeError"
    return str(n)


print(reflected())
print(probe_len(Sized()))
print(len(Counted()))
