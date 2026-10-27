import re
from typing import reveal_type


def f(s: str) -> int:
    if (m := re.match(r"\d+", s)) is None:
        reveal_type(m)
        return -1
    reveal_type(m)
    return len(m.group())


def g(d: dict[str, int | None], k: str) -> int:
    if (v := d.get(k)) is not None and v > 0:
        reveal_type(v)
        return v
    reveal_type(v)
    return 0


def h(xs: list[int | None]) -> int:
    total = 0
    for x in xs:
        if x is None:
            continue
        reveal_type(x)
        total += x
    else:
        reveal_type(x)
    return total


print(f("12a"), f("a"), g({"a": 2}, "a"), g({}, "z"), h([1, None, 2]))
