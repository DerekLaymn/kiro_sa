from typing import reveal_type  # noqa

from dataclasses import KW_ONLY, dataclass, field


@dataclass
class Base:
    a: int
    _: KW_ONLY
    b: str = "b"


@dataclass
class Child(Base):
    c: float = 1.0


def build() -> Child:
    # c is positional (after a), b is kw-only inherited
    return Child(1, 2.5, b="x")


child = build()
reveal_type(child.c)
reveal_type(Child.__init__)
print(child)
