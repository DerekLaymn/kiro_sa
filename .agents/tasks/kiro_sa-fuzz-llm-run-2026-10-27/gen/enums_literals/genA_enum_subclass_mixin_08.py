from typing import reveal_type  # noqa

from enum import Enum


class Base(Enum):
    def describe(self) -> str:
        return f"{self.name}={self.value}"


class Ext(Base):
    A = 1


class Mixed(str, Enum):
    X = "x"
    Y = "y"


def go() -> None:
    reveal_type(Ext.A.describe())
    reveal_type(Mixed.X.upper())
    reveal_type(Mixed.X == "x")
    reveal_type(Mixed.X.value)
    s: str = Mixed.Y
    print(s, Ext.A.describe(), Mixed("x"))


go()
