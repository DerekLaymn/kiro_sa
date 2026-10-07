# area: generics_variance
# explores: type[T] with an upper bound, unions of class objects, type(obj) round-trips
from typing import reveal_type


class Animal:
    def __init__(self) -> None:
        self.sound = "..."


class Dog(Animal):
    def __init__(self) -> None:
        super().__init__()
        self.sound = "woof"


def make[T: Animal](cls: type[T]) -> T:
    return cls()


def make_either(cls: type[int] | type[str]) -> int | str:
    return cls()


def clone_type[T](obj: T) -> type[T]:
    return type(obj)


d = make(Dog)
reveal_type(d)  # Dog
reveal_type(make_either(int))  # int | str
reveal_type(clone_type(d))  # type[Dog]
reveal_type(type(d))  # type[Dog]
print(d.sound, make_either(str) == "", clone_type(d)().sound)
make(int)  # expect-error: int is not an Animal (runs fine)
