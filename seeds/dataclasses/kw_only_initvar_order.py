# area: dataclasses
# hypothesis: field ordering with KW_ONLY, InitVar, defaults in base vs subclass, frozen inheritance.
# spec: typing spec, dataclasses.html; CPython is the oracle for synthesized __init__.
from dataclasses import KW_ONLY, InitVar, dataclass, field
from typing import reveal_type


@dataclass
class Base:
    a: int
    b: int = 0


@dataclass
class Child(Base):
    _: KW_ONLY
    c: int  # ok: keyword-only fields may follow defaulted fields
    scale: InitVar[int] = 1
    tags: list[str] = field(default_factory=list)

    def __post_init__(self, scale: int) -> None:
        self.a *= scale


@dataclass(frozen=True)
class Frozen:
    x: int


ch = Child(1, 2, c=3, scale=2)
reveal_type(Child.__init__)
print(ch, ch.a)
try:
    Child(1, 2, 3)  # expect-error: c is keyword-only
except TypeError as exc:
    print('runtime:', type(exc).__name__)
f = Frozen(1)
try:
    f.x = 2  # expect-error: frozen
except Exception as exc:
    print(type(exc).__name__)
