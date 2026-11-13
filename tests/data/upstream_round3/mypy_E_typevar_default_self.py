from typing import Generic, TypeVar

T = TypeVar("T", default="T")

class C(Generic[T]): ...
