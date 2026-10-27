from typing import reveal_type


def f(x: int | str | bytes | None) -> str:
    if isinstance(x, (int, bytes)):
        reveal_type(x)
        return "ib"
    reveal_type(x)
    if x is None:
        return "none"
    reveal_type(x)
    return x


def g(x: object) -> int:
    if isinstance(x, (list, tuple)):
        reveal_type(x)
        return len(x)
    if isinstance(x, (int, str)) and not isinstance(x, bool):
        reveal_type(x)
        return 1
    return 0


print(f(1), f(b"a"), f(None), f("s"))
print(g([1]), g((1, 2)), g(True), g("a"), g(2.0))
