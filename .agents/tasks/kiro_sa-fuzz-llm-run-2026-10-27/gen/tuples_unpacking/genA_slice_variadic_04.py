from typing import reveal_type  # noqa

def go(t: tuple[int, *tuple[str, ...], bytes], u: tuple[int, ...]) -> None:
    reveal_type(t[0])
    reveal_type(t[-1])
    reveal_type(t[1])
    reveal_type(t[:2])
    reveal_type(t[1:])
    reveal_type(u[:2])
    reveal_type(u[0])


go((1, "a", b"x"), (1, 2))
