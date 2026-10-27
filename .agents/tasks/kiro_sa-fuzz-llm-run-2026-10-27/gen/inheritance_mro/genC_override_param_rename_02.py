from typing import reveal_type


class Base:
    def f(self, x: int) -> int:
        return x


class Sub(Base):
    def f(self, y: int) -> int:  # LSP violation for keyword calls
        return y + 1


def call(b: Base) -> int:
    return b.f(x=1)


print(call(Base()))
try:
    print(call(Sub()))
except TypeError:
    print("TypeError")
reveal_type(Sub().f(2))
