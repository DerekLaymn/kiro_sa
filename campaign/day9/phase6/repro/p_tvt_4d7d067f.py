# area: typevartuple_unpack
# hypothesis: Concatenating variadic tuples with tuple[*Ts, *Us] keeps the element order of both arguments in the inferred return type.
# origin: llm
# area: typevartuple_unpack
# hypothesis: Concatenating variadic tuples with tuple[*Ts, *Us] keeps the element order of both arguments in the inferred return type.
from typing import TypeVarTuple, reveal_type, assert_type

Ts = TypeVarTuple("Ts")
Us = TypeVarTuple("Us")


def concat(a: tuple[*Ts], b: tuple[*Us]) -> tuple[*Ts, *Us]:
    return (*a, *b)


def reverse_pair(a: tuple[*Ts], b: tuple[*Us]) -> tuple[*Us, *Ts]:
    return (*b, *a)


c = concat((1, "x"), (2.0, None))
reveal_type(c)
assert_type(c, tuple[int, str, float, None])
print(c)

r = reverse_pair((1, "x"), (2.0,))
reveal_type(r)
print(r)
