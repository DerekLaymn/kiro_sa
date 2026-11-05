import sys
print(sys.version)
tests = {
    "pep695 *Ts, **P=[bool]": "class A[*Ts, **P = [bool]]: ...",
    "pep695 *Ts=..., **P=[bool] (spec example)": "class A[*Ts = *tuple[int, str], **P = [float, bool]]: ...",
    "pep695 *Ts, T=int": "class A[*Ts, T = int]: ...",
}
for name, src in tests.items():
    try:
        exec(src, {})
        print("OK   ", name)
    except Exception as e:
        print("FAIL ", name, type(e).__name__, e)
from typing import Generic, ParamSpec, TypeVarTuple, Unpack
Ts = TypeVarTuple("Ts")
P = ParamSpec("P", default=[bool])
try:
    class B(Generic[Unpack[Ts], P]): ...
    print("OK    legacy Generic[*Ts, P(default)]")
except Exception as e:
    print("FAIL  legacy Generic[*Ts, P(default)]", type(e).__name__, e)
