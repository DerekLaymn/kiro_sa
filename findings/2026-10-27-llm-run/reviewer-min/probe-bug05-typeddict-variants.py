from collections.abc import Iterable
from typing import Generic, TypedDict, TypeVar, assert_type

T = TypeVar("T")


class Resp(TypedDict, Generic[T]):  # old-style generic TypedDict
    data: T


class Burrow[U](TypedDict):  # PEP 695 generic TypedDict
    resident: U


class Box(Generic[T]):  # control: ordinary generic class
    def __init__(self, v: T) -> None:
        self.v = v


def first_old(r: Resp[T]) -> T:
    return r["data"]


def first_new[X](b: Burrow[X]) -> X:
    return b["resident"]


def unbox(b: Box[T]) -> T:
    return b.v


def gerbil[K, X](homes: dict[K, Burrow[X]] | Iterable[tuple[K, Burrow[X]]]) -> X:
    raise NotImplementedError


def check(a: Resp[int], b: Burrow[int], c: Box[int]) -> None:
    assert_type(first_old(a), int)  # old-style TypedDict param
    assert_type(first_new(b), int)  # PEP 695 TypedDict param
    assert_type(unbox(c), int)  # control: ordinary generic class
    assert_type(gerbil({"vole": b}), int)  # the repro from ty#4803
