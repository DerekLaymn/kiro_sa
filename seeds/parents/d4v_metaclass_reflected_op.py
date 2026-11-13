# area: constructors_metaclasses
# hypothesis: When the metaclass of the right operand subclasses the metaclass of the left operand and overrides the reflected method, CPython calls the reflected method first for A * B on class objects; mypy applies this rule to instances but not to class objects (pyright declines it by design, ty implements it).
# origin: results/bugs.md section 2 (day-3 seed-229f1d38c10b, d3p_constructors_metaclasses_reflected_operator_on_metaclass__mut0_848753c0)
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
