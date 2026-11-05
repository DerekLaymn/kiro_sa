from typing import reveal_type


class Bumper:
    def __set__(self, obj: "Thing", value: int) -> None:
        obj.base += value


class Thing:
    bumped = Bumper()

    def __init__(self, base: int) -> None:
        self.base = base

    def bump(self, value: int) -> None:
        self.base += value

    @property
    def readonly(self) -> int:
        return self.base


def via_descriptor() -> None:
    t = Thing(4)
    assert t.base == 4
    t.bumped = 3
    reveal_type(t.base)
    assert t.base == 7
    t.readonly = 5  # expect-error


def via_method() -> None:
    t = Thing(4)
    assert t.base == 4
    t.bump(3)
    reveal_type(t.base)
    assert t.base == 7
    t.readonly = 5  # expect-error


for fn in (via_descriptor, via_method):
    try:
        fn()
    except AttributeError as e:
        print(fn.__name__, "AttributeError:", e)
