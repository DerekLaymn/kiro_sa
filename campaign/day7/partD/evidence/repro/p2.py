from dataclasses import dataclass


@dataclass
class Wrap:
    value: int


def f(s: Wrap | tuple[int, int]) -> int:
    match s:
        case (a, b):
            return a + b
        case _:
            return s.value


print(f((1, 2)), f(Wrap(3)))
