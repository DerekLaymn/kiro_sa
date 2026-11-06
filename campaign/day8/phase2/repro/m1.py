"""Day 8 morning: where does ty's `list[str]` for `rest` come from? (Day-7 match_statement live item)"""
from typing import reveal_type


class Point:
    x: int = 0


def f1(s: list[int] | str) -> None:
    match s:
        case [first, *rest]:
            reveal_type(rest)  # CPython: only the list can match, a str never matches a sequence pattern


def f2(s: list[int] | int) -> None:
    match s:
        case [first, *rest]:
            reveal_type(rest)


def f3(s: Point | list[int]) -> None:
    match s:
        case Point():
            pass
        case [first, *rest]:
            reveal_type(rest)  # Point is not final: a subclass of Point could also be a Sequence


def f4(s: Point | dict[str, int]) -> None:
    match s:
        case {"k": v, **others}:
            reveal_type(others)


def f5(s: list[int] | str) -> None:
    match s:
        case Point():
            pass
        case _:
            reveal_type(s)
