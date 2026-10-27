from typing import reveal_type


class Base:
    items: list[object]
    value: int | str

    def __init__(self) -> None:
        self.items = []
        self.value = 1


class Sub(Base):
    items: list[int]  # type: ignore
    value: int  # type: ignore

    def __init__(self) -> None:
        super().__init__()
        self.items = [1]
        self.value = 2


def poison(b: Base) -> None:
    b.items.append("x")
    b.value = "s"


s = Sub()
poison(s)
reveal_type(s.items)
reveal_type(s.value)
print(s.items, s.value)
try:
    print(sum(s.items))  # type: ignore
except TypeError:
    print("TypeError")
