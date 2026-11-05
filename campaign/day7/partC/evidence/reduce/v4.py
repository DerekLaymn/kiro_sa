from typing import reveal_type
def g() -> int:
    raise ValueError
def f() -> None:
    value: int | str = 1
    try:
        value, other = "bad", g()
    except ValueError:
        reveal_type(value)
f()
