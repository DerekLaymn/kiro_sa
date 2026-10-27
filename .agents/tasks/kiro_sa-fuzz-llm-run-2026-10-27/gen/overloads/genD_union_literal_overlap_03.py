from typing import Literal, overload, reveal_type


@overload
def m(x: Literal["a"]) -> int: ...
@overload
def m(x: Literal["b", "c"]) -> bytes: ...
@overload
def m(x: str) -> str: ...
def m(x: str) -> int | bytes | str:
    if x == "a":
        return 1
    if x in ("b", "c"):
        return b"x"
    return x


def f(k: Literal["a", "b"], s: str, t: Literal["a", "z"]) -> None:
    reveal_type(m(k))
    reveal_type(m(s))
    reveal_type(m(t))
    reveal_type(m("c"))


f("a", "q", "z")
print(m("a"), m("b"), m("zz"))
