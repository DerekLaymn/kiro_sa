# area: typevartuple_unpack
# hypothesis: Generic[*Ts, P] with a defaulted ParamSpec after a TypeVarTuple raises TypeError at runtime in 3.13, while ty and mypy accept it and disagree on every reveal. Vary: a defaulted TypeVar after *Ts, PEP 695 class Callback[*Ts, **P = [bool]], P before *Ts.
# origin: harvested program seed-570818101ed2 (ruff mdtest generics/legacy/typevartuple.md block 30; runtime_miss + reveal mismatches)
from typing import Any, Callable, Concatenate, Generic, ParamSpec, TypeVarTuple

Ts = TypeVarTuple("Ts")
P = ParamSpec("P", default=[bool])

class Callback(Generic[*Ts, P]):
    fn: Callable[P, tuple[*Ts]]

reveal_type(Callback[int, str]().fn)  # revealed: (bool, /) -> tuple[int, str]
reveal_type(Callback[list[int]]().fn)  # revealed: (bool, /) -> tuple[list[int]]
reveal_type(Callback[int, [str]]().fn)  # revealed: (str, /) -> tuple[int]
reveal_type(Callback[int, [str], *tuple[()]]().fn)  # revealed: (str, /) -> tuple[int]
reveal_type(Callback[...]().fn)  # revealed: (...) -> tuple[()]

Q = ParamSpec("Q")

def forward(a: Callback[int, Q], b: Callback[str, Concatenate[int, Q]]) -> None:
    reveal_type(a.fn)  # revealed: (**Q@forward) -> tuple[int]
    reveal_type(b.fn)  # revealed: (int, /, *args: Q@forward.args, **kwargs: Q@forward.kwargs) -> tuple[str]
