# area: constructors_metaclasses
# hypothesis: A metaclass __call__ that returns an unrelated type replaces the constructor result, so calls through type[Box] do not yield Box instances.
# origin: llm
# Hypothesis: a metaclass __call__ returning an unrelated type replaces the constructor result, so type[Box] calls do not produce Box instances.
from typing import reveal_type


class Meta(type):
    def __call__(cls, value: int) -> str:
        return 'wrapped:' + str(value * 2)


class Box(metaclass=Meta):
    def __new__(cls, value: int) -> 'Box':
        return super().__new__(cls)

    def __init__(self, value: int) -> None:
        self.value = value


def make(kind: type[Box], n: int) -> Box:
    return kind(n)


b = Box(5)
reveal_type(b)
print(b)
print(make(Box, 5))
inst = Box.__new__(Box, 1)
Box.__init__(inst, 1)
print(type(inst).__name__, inst.value)
