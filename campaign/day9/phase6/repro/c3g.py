from typing import assert_type


class Base:
    def __lt__(self, other: "Base") -> str:
        return "lt"


class Child(Base):
    def __gt__(self, other: "Child") -> int:
        return 7


a = Child()
b = Child()
s: str = a < b
assert_type(a < b, str)
assert_type(a > b, int)
print(repr(a < b), repr(a > b))
