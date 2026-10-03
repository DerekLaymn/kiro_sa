# area: protocols
# hypothesis: a protocol *attribute* (settable) is not satisfied by a read-only property,
# while a protocol *property* is satisfied by a plain attribute.
# spec: typing spec, protocol.html "Protocol members".
from typing import Protocol


class HasName(Protocol):
    name: str


class HasReadOnlyName(Protocol):
    @property
    def name(self) -> str: ...


class Plain:
    def __init__(self) -> None:
        self.name = "plain"


class ReadOnly:
    @property
    def name(self) -> str:
        return "ro"


def rename(x: HasName) -> None:
    x.name = "new"


def show(x: HasReadOnlyName) -> str:
    return x.name


print(show(Plain()), show(ReadOnly()))
rename(Plain())
try:
    rename(ReadOnly())  # expect-error: read-only property cannot satisfy a settable attribute
except AttributeError as exc:
    print("runtime:", exc)
