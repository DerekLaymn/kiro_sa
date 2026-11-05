from typing import Generic, TypeVar, TypeVarTuple, Unpack

Ts = TypeVarTuple("Ts")
T = TypeVar("T", default=int)


class Pack(Generic[Unpack[Ts], T]): ...


Pack[int, str]
