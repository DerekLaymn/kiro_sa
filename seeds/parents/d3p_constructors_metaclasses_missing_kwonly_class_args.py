# area: constructors_metaclasses
# hypothesis: A metaclass __new__ with required keyword-only parameters: a class statement that omits them raises TypeError at runtime; only pyright reports the missing arguments (mypy and ty are silent). Vary: **kwargs, a default value, __init_subclass__ instead of a metaclass, a wrong keyword type.
# origin: runs/day2/out3 seed-1cadfac7cbe5 (pyright tests/samples/metaclass9.py; runtime_miss, trimmed to the construct)
from typing import Any


class Meta1(type):
    def __new__(mcs, name: str, bases: tuple[type, ...], attrs: dict[str, Any], *, param1: int, param2: str) -> "Meta1":
        return super().__new__(mcs, name, bases, attrs)

    def __init__(cls, name: str, bases: tuple[type, ...], attrs: dict[str, Any], *, param1: int, param2: str) -> None:
        super().__init__(name, bases, attrs)


class Class1_1(metaclass=Meta1, param1=1, param2=""): ...


class Class1_4(metaclass=Meta1): ...  # runtime: TypeError, missing keyword-only arguments
