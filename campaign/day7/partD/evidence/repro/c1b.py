from typing import reveal_type


def unpack(items: tuple[int, ...]) -> None:
    value: int | str = 1
    try:
        value, (a, b) = "bad", items
    except ValueError:
        reveal_type(value)


def chained(items: list[int | str]) -> None:
    value: int | str = 1
    try:
        value = items[5] = "bad"
    except IndexError:
        reveal_type(value)


def subscript(items: list[int | str]) -> None:
    value: int | str = 1
    try:
        value, items[5] = "bad", 2
    except IndexError:
        reveal_type(value)


unpack((1,))
chained([1])
subscript([1])
