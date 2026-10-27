from typing import reveal_type  # noqa

def go(t: tuple[int, str, float, bytes, bool]) -> None:
    reveal_type(t[1:3])
    reveal_type(t[:-1])
    reveal_type(t[::2])
    reveal_type(t[-2:])
    reveal_type(t[::-1])
    reveal_type(t[3:1])
    reveal_type(t[-1])


go((1, "s", 2.0, b"b", True))
