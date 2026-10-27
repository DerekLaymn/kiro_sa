from typing import Protocol, reveal_type


class CB(Protocol):
    def __call__(self, *, x: int) -> int: ...


def f1(x: int) -> int:
    return x


def f2(y: int) -> int:
    return y


a: CB = f1  # OK
b: CB = f2  # error: name mismatch
reveal_type(a)
print(a(x=1), b(x=1) if False else 0)
