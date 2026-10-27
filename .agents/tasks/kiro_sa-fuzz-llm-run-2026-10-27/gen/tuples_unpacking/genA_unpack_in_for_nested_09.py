from typing import reveal_type  # noqa

def go(rows: list[tuple[int, tuple[str, float]]], d: dict[str, tuple[int, ...]]) -> None:
    for i, (s, f) in rows:
        reveal_type(s)
        reveal_type(f)
    for k, (first, *rest) in d.items():
        reveal_type(first)
        reveal_type(rest)
    pairs = list(zip([1], ["a"], [2.0]))
    reveal_type(pairs)
    for p, q, r in pairs:
        reveal_type(r)
    print(rows, d)


go([(1, ("a", 1.0))], {"k": (1, 2, 3)})
