from typing import reveal_type


class Base:
    def __init__(self, tag: str = "base") -> None:
        self.tag = tag

    @classmethod
    def make(cls) -> "Base":
        return cls("made")


class Sub(Base):
    @classmethod
    def make(cls) -> "Sub":
        r = super().make()
        reveal_type(r)
        assert isinstance(r, Sub)
        return r


s = Sub.make()
reveal_type(s)
print(type(s).__name__, s.tag)
