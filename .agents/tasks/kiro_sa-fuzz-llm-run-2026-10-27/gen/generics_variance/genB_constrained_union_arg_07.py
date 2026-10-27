from typing import reveal_type


def ident[T: (int, str)](x: T) -> T:
    return x


def caller(v: int | str) -> None:
    r = ident(v)  # error
    reveal_type(r)


caller(1)
caller("s")
