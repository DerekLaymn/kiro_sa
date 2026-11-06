from typing import reveal_type


class Base:
    def __le__(self, other: "Base") -> str:
        return "le"


class Child(Base):
    def __ge__(self, other: "Child") -> int:
        return 7


class Sub(Child):
    pass


a = Child()
b = Child()
reveal_type(a <= b)
print(repr(a <= b))
# control: right operand is a proper subclass that overrides the reflected method
c = Sub()
reveal_type(a <= c)
print(repr(a <= c))
