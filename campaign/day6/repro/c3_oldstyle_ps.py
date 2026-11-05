from typing import Generic, ParamSpec, TypeVarTuple, Unpack

Ts = TypeVarTuple("Ts")
P = ParamSpec("P", default=[bool])


class Callback(Generic[Unpack[Ts], P]): ...


Callback[int, str]
