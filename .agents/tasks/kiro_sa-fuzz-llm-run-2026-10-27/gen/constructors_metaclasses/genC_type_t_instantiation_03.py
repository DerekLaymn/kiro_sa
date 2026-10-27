from typing import TypeVar, reveal_type


class Animal:
    def __init__(self, name: str) -> None:
        self.name = name


class Dog(Animal):
    def __init__(self, name: str, tricks: int = 0) -> None:
        super().__init__(name)
        self.tricks = tricks


A = TypeVar("A", bound=Animal)


def make(cls: type[A], name: str) -> A:
    return cls(name)


def make_bad(cls: type[A]) -> A:
    return cls()  # type: ignore


d = make(Dog, "rex")
reveal_type(d)
print(d.name, d.tricks)
try:
    make_bad(Dog)
except TypeError:
    print("TypeError")
reveal_type(make(Animal, "a"))
