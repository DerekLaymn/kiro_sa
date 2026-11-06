# area: typevartuple_unpack
# hypothesis: A non-type argument in a Generic subscription that mixes a TypeVarTuple with a defaulted ParamSpec raises TypeError at runtime, while checkers may not flag it.
# origin: runs/day9/parents/C_tvt/d3p_typevartuple_unpack_paramspec_default_after_tvt.py
# area: typevartuple_unpack
# hypothesis: a non-type argument in a Generic subscription that mixes a TypeVarTuple with a defaulted ParamSpec is rejected at runtime with TypeError, while checkers may not flag it.
from typing import Callable, Generic, ParamSpec, TypeVarTuple, reveal_type

Ts = TypeVarTuple('Ts')
P = ParamSpec('P', default=[bool])


class Callback(Generic[*Ts, P]):
    fn: Callable[P, tuple[*Ts]]


ok = Callback[int, str]()
reveal_type(ok)
print(type(Callback[list[int]]()).__name__)
print(type(Callback[int, [str]]()).__name__)

try:
    bad = Callback[int, 3]()  # expect-error: 3 is not a valid ParamSpec argument
except TypeError as exc:
    print('bad form:', type(exc).__name__)
