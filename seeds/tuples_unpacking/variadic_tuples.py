# area: tuples_unpacking
# hypothesis: unbounded-tuple unpacking, star-unpack in tuple types, slicing, and NamedTuple indexing.
# spec: typing spec, tuples.html.
from typing import NamedTuple, reveal_type


class Row(NamedTuple):
    id: int
    name: str
    score: float = 0.0


def split(t: tuple[int, *tuple[str, ...], float]) -> None:
    head, *mid, tail = t
    reveal_type(head)  # int
    reveal_type(mid)  # list[str]
    reveal_type(tail)  # float
    reveal_type(t[1:])  # tuple[*tuple[str, ...], float]
    reveal_type(t[-1])  # float


r = Row(1, "a")
reveal_type(r[1])  # str
reveal_type(r[-1])  # float
i, n, s = r
reveal_type(s)
split((1, "a", "b", 2.0))
print(r, i, n, s)
x, y = (1, 2, 3)  # expect-error: too many values to unpack (crashes at runtime)
