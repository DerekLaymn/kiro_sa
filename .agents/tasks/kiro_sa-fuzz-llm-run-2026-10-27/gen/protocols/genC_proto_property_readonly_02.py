from dataclasses import dataclass
from typing import Protocol, reveal_type


class HasName(Protocol):
    @property
    def name(self) -> str: ...


class HasMutableName(Protocol):
    name: str


@dataclass(frozen=True)
class Frozen:
    name: str


class WithProp:
    @property
    def name(self) -> str:
        return "p"


class Plain:
    def __init__(self) -> None:
        self.name = "plain"


def read(x: HasName) -> str:
    reveal_type(x.name)
    return x.name


def write(x: HasMutableName) -> None:
    x.name = "changed"
    reveal_type(x.name)


print(read(Frozen("f")), read(WithProp()), read(Plain()))
p = Plain()
write(p)
print(p.name)
try:
    write(WithProp())  # type: ignore
except AttributeError as e:
    print("AttributeError")
