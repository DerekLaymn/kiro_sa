from typing import Protocol, TypeVar, reveal_type

T = TypeVar("T")


class Source(Protocol[T]):
    def get(self) -> T: ...

    def get_or(self, default: T) -> T:
        return self.get() if self.get() is not None else default


class IntSource(Source[int]):
    def get(self) -> int:
        return 3


class Structural:
    def get(self) -> str:
        return "s"


def use(s: Source[str]) -> str:
    return s.get()


a = IntSource()
reveal_type(a.get_or(4))
print(a.get_or(4))
print(use(Structural()))
b: Source[int] = IntSource()
reveal_type(b.get_or(1))
print(b.get_or(1))
