from typing import reveal_type
def f() -> None:
    value: int | str = 1
    try:
        value = "bad"
        int("x")
    except ValueError:
        reveal_type(value)
f()
