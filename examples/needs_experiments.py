# Hypothesis: (1) ty's default ==-narrowing is a documented unsound default (resolved by a config
# toggle experiment); (2) mutable attribute override + aliasing fails at runtime while BOTH
# checkers stay silent -> RUNTIME_MISS that only adjudication (or a human) can classify.
from typing import Literal


def parse(value: str) -> Literal["a"] | None:
    if value == "a":
        return value  # mypy: return-value; ty: narrowed to Literal["a"] by default
    return None


class Base:
    attr: object = 0


class Child(Base):
    attr: str = "x"  # covariant override of a mutable attribute


def clobber(b: Base) -> None:
    b.attr = 1


print(parse("a"))
c = Child()
clobber(c)
print(c.attr.upper())  # AttributeError at runtime: 'int' object has no attribute 'upper'
