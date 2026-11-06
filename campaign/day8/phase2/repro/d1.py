"""Day 8 morning: the Day-7 dataclasses live family (11 findings, 7 programs, all `overloaded_post_init` mutants).
mypy: `__post_init__` parameter type incompatible with the InitVar field. ty / pyright: ?"""
from dataclasses import InitVar, dataclass


@dataclass
class A:
    value: InitVar[int]

    def __post_init__(self, value: str) -> None:  # InitVar[int] is passed, str is declared
        print(value.upper())


@dataclass
class B:
    value: InitVar[int]

    def __post_init__(self, value: int, extra: int) -> None:  # one parameter too many
        print(value, extra)


try:
    A(1)
except AttributeError as e:
    print("A:", e)
try:
    B(1)
except TypeError as e:
    print("B:", e)
