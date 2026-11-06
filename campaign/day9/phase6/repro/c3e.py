from typing import reveal_type


class Base:
    def __add__(self, other: "Base") -> str:
        return "add"


class Child(Base):
    def __radd__(self, other: "Base") -> int:
        return 7


a = Child()
b = Child()
reveal_type(a + b)
print(repr(a + b))
