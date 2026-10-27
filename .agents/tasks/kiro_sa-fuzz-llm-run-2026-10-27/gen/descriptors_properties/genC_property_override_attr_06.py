from typing import reveal_type


class Base:
    @property
    def v(self) -> int:
        return 1


class Sub(Base):
    v: int = 5  # type: ignore


class Base2:
    v: int = 1


class Sub2(Base2):
    @property
    def v(self) -> int:  # type: ignore
        return 2


print(Sub().v)
reveal_type(Sub().v)
s2 = Sub2()
reveal_type(s2.v)
try:
    s2.v = 3
except AttributeError:
    print("AttributeError")
print(s2.v)
