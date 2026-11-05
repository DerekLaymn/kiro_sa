from typing import reveal_type
def f() -> None:
    value: int | str = 1
    try:
        value = "bad"
        raise ValueError
    except ValueError:
        reveal_type(value)
f()
