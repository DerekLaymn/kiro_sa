from typing import TypeVar

T = TypeVar("T")


class A(Base[T]):
    pass


class Base: ...
