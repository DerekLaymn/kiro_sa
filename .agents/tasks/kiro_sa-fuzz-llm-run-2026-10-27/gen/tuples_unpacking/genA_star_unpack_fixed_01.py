from typing import reveal_type  # noqa

def go(t: tuple[int, str, float, bytes]) -> None:
    a, *mid, z = t
    reveal_type(a)
    reveal_type(mid)
    reveal_type(z)
    *head, last = t
    reveal_type(head)
    first, *rest = t
    reveal_type(rest)
    print(a, mid, z, head, last, first, rest)


go((1, "s", 2.0, b"b"))
