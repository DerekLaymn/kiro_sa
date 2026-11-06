from functools import total_ordering
from typing import reveal_type


class Base:
    def __lt__(self, other: "Base") -> str:
        return "lt"


@total_ordering
class Child(Base):
    pass


a = Child()
b = Child()
reveal_type(a < b)
reveal_type(a >= b)
print(repr(a < b))
