import enum
from typing import Generic, TypedDict, TypeVar

T = TypeVar("T")


class F(enum.Flag):
    R = 1
    W = 2


print(repr(F.R & F.W), repr(F.R ^ F.R))


class Resp(TypedDict, Generic[T]):
    data: T


def takes_int(r: Resp[int]) -> None: ...


def go(c: Resp[str]) -> None:
    takes_int(c)
    z: Resp[int] = c
