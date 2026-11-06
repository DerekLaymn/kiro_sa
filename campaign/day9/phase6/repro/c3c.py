from typing import reveal_type


class Base:
    def __lt__(self, other: "Base") -> str:
        return "lt"


class Child(Base):
    def __gt__(self, other: "Child") -> int:
        return 7


a = Child()
b = Child()
reveal_type(a < b)
reveal_type(a > b)
print(repr(a < b), repr(a > b))
