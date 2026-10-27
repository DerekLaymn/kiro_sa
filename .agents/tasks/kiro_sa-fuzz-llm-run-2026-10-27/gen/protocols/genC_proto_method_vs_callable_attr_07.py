from typing import Callable, Protocol, reveal_type


class Op(Protocol):
    def apply(self, x: int) -> int: ...


class ViaAttr:
    def __init__(self) -> None:
        self.apply: Callable[[int], int] = lambda x: x + 1


class ViaStatic:
    @staticmethod
    def apply(x: int) -> int:
        return x * 2


class ViaClassAttr:
    apply: Callable[[int], int] = lambda x: x - 1  # becomes a method at runtime


def run(o: Op) -> int:
    return o.apply(10)


print(run(ViaAttr()))
print(run(ViaStatic()))
try:
    print(run(ViaClassAttr()))
except TypeError:
    print("TypeError")
reveal_type(run(ViaAttr()))
