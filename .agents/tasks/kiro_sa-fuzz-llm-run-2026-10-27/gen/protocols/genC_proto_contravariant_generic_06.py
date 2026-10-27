from typing import Protocol, TypeVar, reveal_type

T_contra = TypeVar("T_contra", contravariant=True)
T_co = TypeVar("T_co", covariant=True)


class Consumer(Protocol[T_contra]):
    def eat(self, x: T_contra) -> None: ...


class Producer(Protocol[T_co]):
    def make(self) -> T_co: ...


class ObjEater:
    def eat(self, x: object) -> None:
        print("ate", x)


class IntMaker:
    def make(self) -> int:
        return 7


def feed(c: Consumer[int]) -> None:
    c.eat(1)


def get(p: Producer[float]) -> float:
    return p.make()


feed(ObjEater())
reveal_type(get(IntMaker()))
print(get(IntMaker()))
c2: Consumer[bool] = ObjEater()
c2.eat(True)
p2: Producer[object] = IntMaker()
reveal_type(p2.make())
