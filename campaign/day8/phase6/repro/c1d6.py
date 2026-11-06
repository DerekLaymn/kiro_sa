from typing import reveal_type


def f(pair: tuple[int, ...]) -> None:
    value: int | str = 1
    try:
        value, (a, b) = "bad", pair
    except ValueError:
        reveal_type(value)
        print(repr(value))


f((1,))
