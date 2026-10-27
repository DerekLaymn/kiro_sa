from typing import overload, reveal_type


@overload
def conv(x: int) -> str: ...
@overload
def conv(x: str) -> int: ...
def conv(x: int | str) -> int | str:
    return str(x) if isinstance(x, int) else len(x)


def f(v: int | str, w: int | str | bytes) -> None:
    reveal_type(conv(v))
    if isinstance(w, bytes):
        return
    reveal_type(conv(w))


def g(vs: list[int | str]) -> None:
    for v in vs:
        reveal_type(conv(v))


f(1, "a")
g([1, "abc"])
print(conv(5), conv("abc"))
