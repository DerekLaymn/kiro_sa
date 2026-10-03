# area: narrowing_builtin
# hypothesis: narrowing via len() on tuple unions, `in` on Literal unions, walrus, and early return.
# spec: typing spec, narrowing.html (len narrowing of tuples is specified behaviour of major checkers).
from typing import Literal, reveal_type


def by_len(t: tuple[int] | tuple[int, str]) -> None:
    if len(t) == 2:
        reveal_type(t)  # tuple[int, str]
        print(t[1].upper())
    else:
        reveal_type(t)  # tuple[int]


def by_in(mode: Literal["r", "w", "a"]) -> None:
    if mode in ("r", "w"):
        reveal_type(mode)  # Literal["r", "w"]
    else:
        reveal_type(mode)  # Literal["a"]


def by_walrus(d: dict[str, int | None]) -> int:
    if (v := d.get("k")) is not None:
        reveal_type(v)  # int
        return v
    reveal_type(v)  # int | None  (None)
    return 0


by_len((1, "a"))
by_len((1,))
by_in("a")
print(by_walrus({"k": 3}), by_walrus({}))
