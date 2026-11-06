from typing import TypeVarTuple, reveal_type

Ts = TypeVarTuple("Ts")
Us = TypeVarTuple("Us")


def concat(a: tuple[*Ts], b: tuple[*Us]) -> tuple[*Ts, *Us]:
    return (*a, *b)


reveal_type(concat((1, "x"), (2.0, None)))
print(concat((1, "x"), (2.0, None)))
