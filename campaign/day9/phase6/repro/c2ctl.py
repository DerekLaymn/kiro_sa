from typing import TypeVarTuple, reveal_type

Ts = TypeVarTuple("Ts")


def prepend(a: tuple[*Ts]) -> tuple[int, *Ts]:
    return (0, *a)


reveal_type(prepend((1, "x")))
print(prepend((1, "x")))
