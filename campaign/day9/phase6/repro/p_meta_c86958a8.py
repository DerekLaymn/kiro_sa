# area: constructors_metaclasses
# hypothesis: A metaclass __call__ annotated to return int makes Widget('abc') evaluate to int at runtime, so checkers that ignore the metaclass return type will wrongly infer Widget.
# origin: llm
# Hypothesis: a metaclass __call__ annotated to return int makes Widget('abc') evaluate to int, so checkers that ignore that return type infer Widget instead.
from typing import TypeVar, reveal_type

T = TypeVar('T')


class Counting(type):
    def __call__(cls, *args: str) -> int:
        inst = super().__call__(*args)
        return len(inst.name)


class Widget(metaclass=Counting):
    def __init__(self, name: str) -> None:
        self.name = name


class Pair:
    def __new__(cls, a: int, b: int) -> 'Pair':
        return super().__new__(cls)

    def __init__(self, a: int, b: int) -> None:
        self.total = a + b


class Ticket:
    def __init__(self) -> None:
        self.id = 9


def make(kind: type[T]) -> T:
    return kind()


n = Widget('abc')
reveal_type(n)
assert n == 3

t = make(Ticket)
reveal_type(t)
assert t.id == 9

p = Pair(2, 5)
reveal_type(p)
assert p.total == 7
