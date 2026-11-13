# Bug 3 (mypy): see examples/bugs/README.md for the issue link and the expected/actual result.
from typing import assert_type


class LeftMeta(type):
    def __mul__(cls, other: object) -> int:
        return 1


class RightMeta(LeftMeta):
    def __rmul__(cls, other: object) -> str:
        return "s"


class A(metaclass=LeftMeta): ...
class B(metaclass=RightMeta): ...


s: str = A * B
assert_type(A * B, str)
print(type(A * B).__name__)
