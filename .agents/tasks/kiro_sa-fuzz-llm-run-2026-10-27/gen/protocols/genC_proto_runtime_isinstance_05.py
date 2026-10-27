from typing import Protocol, runtime_checkable, reveal_type


@runtime_checkable
class Sized2(Protocol):
    size: int

    def grow(self) -> None: ...


class Box:
    def __init__(self) -> None:
        self.size = 1

    def grow(self) -> None:
        self.size += 1


class NoGrow:
    size = 3


def f(x: Box | NoGrow | int) -> str:
    if isinstance(x, Sized2):
        reveal_type(x)
        x.grow()
        return "sized"
    reveal_type(x)
    return "other"


print(f(Box()), f(NoGrow()), f(3))
