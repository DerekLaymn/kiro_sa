# area: recursive_aliases (crash hunting: loops whose types grow each iteration)
# hypothesis: control-flow fix-point iteration over loops that widen/nest types terminates
# (ty documents `Divergent` for this; panics or hangs are bugs).
from typing import reveal_type


def grow(n: int) -> object:
    x: object = 0
    y = 0
    z = (0,)
    for _ in range(n):
        x = [x]
        y = (y, y)
        z = z + z
    reveal_type(y)
    reveal_type(z)
    return x


def ping_pong(n: int) -> None:
    a = 1
    b = "s"
    while n > 0:
        a, b = [b], {"k": a}
        n -= 1
    reveal_type(a)
    reveal_type(b)


print(grow(3))
ping_pong(3)
