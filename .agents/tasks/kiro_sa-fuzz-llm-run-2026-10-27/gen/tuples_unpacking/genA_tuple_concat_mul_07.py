from typing import reveal_type  # noqa

def go(a: tuple[int, str], b: tuple[float, ...]) -> None:
    reveal_type(a + a)
    reveal_type(a + b)
    reveal_type(b + a)
    reveal_type(a * 2)
    reveal_type(b * 2)
    reveal_type((1, "x") + (2.0,))
    reveal_type(a + ())
    print(a, b)


go((1, "s"), (1.0,))
