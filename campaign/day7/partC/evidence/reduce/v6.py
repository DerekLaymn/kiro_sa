from typing import reveal_type
def f(items: list[int]) -> None:
    value: int | str = 1
    try:
        value, a, b = "bad", *items
    except ValueError:
        reveal_type(value)
f([1])
