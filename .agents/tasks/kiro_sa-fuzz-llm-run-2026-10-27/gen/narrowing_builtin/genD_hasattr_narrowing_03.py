from typing import reveal_type


class A:
    name: str = "a"


class B:
    pass


def f(x: A | B) -> str:
    if hasattr(x, "name"):
        reveal_type(x)
        return str(x.name)
    reveal_type(x)
    return "none"


def g(x: object) -> int:
    if hasattr(x, "bit_length"):
        reveal_type(x)
        return 1
    return 0


print(f(A()), f(B()), g(3), g("s"))
