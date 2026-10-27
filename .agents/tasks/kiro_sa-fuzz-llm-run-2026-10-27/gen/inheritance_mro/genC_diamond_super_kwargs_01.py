from typing import Any, reveal_type


class Base:
    def __init__(self, **kw: Any) -> None:
        self.trace = ["Base"]

    def who(self) -> str:
        return "Base"


class Left(Base):
    def __init__(self, left: int = 0, **kw: Any) -> None:
        super().__init__(**kw)
        self.trace.append("Left")
        self.left = left

    def who(self) -> str:
        return "Left>" + super().who()


class Right(Base):
    def __init__(self, right: str = "", **kw: Any) -> None:
        super().__init__(**kw)
        self.trace.append("Right")
        self.right = right

    def who(self) -> str:
        return "Right>" + super().who()


class D(Left, Right):
    def who(self) -> str:
        reveal_type(super())
        return "D>" + super().who()


d = D(left=1, right="r")
reveal_type(d.left)
reveal_type(d.right)
print(d.trace, d.who(), [c.__name__ for c in D.__mro__])
