from typing import Unpack, reveal_type

type Row[*Ts] = tuple[int, *Ts]


def mk(r: Row[str, float]) -> None:
    reveal_type(r)
    print(r[0])


mk((1, "a", 2.0))
mk((1, "a"))  # error
x: Row[()] = (1,)
reveal_type(x)
y: tuple[int, Unpack[tuple[str, ...]]] = (1,)
reveal_type(y)
