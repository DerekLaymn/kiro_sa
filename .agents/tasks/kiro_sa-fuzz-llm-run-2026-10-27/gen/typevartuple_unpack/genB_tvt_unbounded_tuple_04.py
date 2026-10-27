from typing import reveal_type


def ident[*Ts](t: tuple[*Ts]) -> tuple[*Ts]:
    return t


def make(n: int) -> tuple[int, ...]:
    return (1,) * n


reveal_type(ident(make(2)))
x: tuple[int, *tuple[str, ...]] = (1, "a", "b")
reveal_type(ident(x))
print(ident(make(2)), ident(x))
