from typing import Protocol, reveal_type


class Factory(Protocol):
    def __call__(self, x: int) -> "Widget": ...


class HasMake(Protocol):
    def make(self, x: int) -> "Widget": ...


class Widget:
    def __init__(self, x: int) -> None:
        self.x = x

    @classmethod
    def make(cls, x: int) -> "Widget":
        return cls(x)


class Other:
    def __init__(self, x: str) -> None:
        self.x = x


def build(f: Factory) -> Widget:
    return f(1)


def build2(m: HasMake) -> Widget:
    return m.make(2)


reveal_type(build(Widget))
print(build(Widget).x)
print(build2(Widget).x)
try:
    build(Other)  # type: ignore
except Exception as e:
    print(type(e).__name__)
reveal_type(Widget.make)
