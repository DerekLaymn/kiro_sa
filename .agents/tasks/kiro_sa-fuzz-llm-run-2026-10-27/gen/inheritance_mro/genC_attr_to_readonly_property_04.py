from typing import reveal_type


class Base:
    def __init__(self) -> None:
        self.n = 1


class Sub(Base):
    @property
    def n(self) -> int:  # type: ignore
        return 5


try:
    s = Sub()
    reveal_type(s.n)
    print(s.n)
except AttributeError:
    print("AttributeError")
