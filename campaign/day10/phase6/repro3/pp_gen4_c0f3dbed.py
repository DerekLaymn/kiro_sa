# area: dunder_dispatch
# hypothesis: CPython looks up special methods on the type, so len() and call syntax ignore dunders assigned on the instance or only annotated, and __getattr__ does not supply dunders, so checkers that accept those forms disagree with the runtime.
# origin: llm
# area: dunder_dispatch
# hypothesis: CPython looks up special methods on the type, so len() and call syntax ignore dunders assigned on the instance or only annotated, and __getattr__ does not supply dunders, so checkers that accept those forms disagree with the runtime.
from typing import Callable, reveal_type


class Base:
    def __len__(self) -> int:
        return 3


class Child(Base):
    pass


class InstanceAssigned:
    def __init__(self) -> None:
        self.__len__ = lambda: 99
        self.__call__ = lambda: 'instance call'


class AnnotationOnly:
    __len__: Callable[[], int]


class Fallback:
    def __getattr__(self, name: str) -> int:
        return 42


def inherited_len() -> int:
    n = len(Child())
    reveal_type(n)
    return n


def instance_len() -> str:
    try:
        return str(len(InstanceAssigned()))  # expect-error
    except TypeError:
        return 'TypeError'


def instance_call() -> str:
    try:
        return InstanceAssigned()()  # expect-error
    except TypeError:
        return 'TypeError'


def annotation_len() -> str:
    try:
        return str(len(AnnotationOnly()))
    except TypeError:
        return 'TypeError'


def getattr_len() -> str:
    try:
        return str(len(Fallback()))  # expect-error
    except TypeError:
        return 'TypeError'


print(inherited_len())
print(instance_len())
print(instance_call())
print(annotation_len())
print(getattr_len())
