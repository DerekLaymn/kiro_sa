from typing import reveal_type  # noqa

def go(t: tuple[int, *tuple[str, ...], float]) -> None:
    a, *mid, z = t
    reveal_type(a)
    reveal_type(mid)
    reveal_type(z)
    x, y, w = t
    reveal_type(y)
    print(a, mid, z, x, y, w)


go((1, "a", 2.0))
