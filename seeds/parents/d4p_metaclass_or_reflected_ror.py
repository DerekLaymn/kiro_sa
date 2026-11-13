# area: constructors_metaclasses
# hypothesis: With metaclass B overriding __ror__ and type(A) a base of type(B), A | B calls the reflected method first at runtime ('right'); mypy picks the left __or__, ty infers a UnionType. Vary: *, +, @ with __rmul__ etc.
# origin: runs/day3/gen/constructors_metaclasses/d3p_constructors_metaclasses_reflected_operator_on_metaclass__mut1_714d2273.py (seed-83edc0d9bc6c); results/days/day3-report.md section 5 item 4
from typing import Literal, reveal_type


class LeftMeta(type):
    def __or__(cls, other: object) -> Literal["left"]:
        return "left"


class RightMeta(LeftMeta):
    def __ror__(cls, other: object) -> Literal["right"]:
        return "right"


class A(metaclass=LeftMeta): ...


class B(metaclass=RightMeta): ...


reveal_type(A | B)
assert (A | B) == "right"
assert (A | A) == "left"
