# area: gradual_any
# origin: ruff mdtest annotations/intersection_types.md block 6
from typing import TypeAlias

A: TypeAlias = "~A & A"  # error: [cyclic-type-alias-definition]
B: TypeAlias = "B & ~B"  # error: [cyclic-type-alias-definition]
C: TypeAlias = "~C"  # error: [cyclic-type-alias-definition]
D: TypeAlias = "D & int"  # error: [cyclic-type-alias-definition]
