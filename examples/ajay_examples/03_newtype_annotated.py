# area: gradual_any (type forms)
# explores: NewType is a distinct subtype of its base; Annotated metadata is transparent to checkers
from typing import Annotated, NewType, reveal_type

UserId = NewType("UserId", int)
Meters = Annotated[float, "unit=m"]


def lookup(uid: UserId) -> str:
    return f"user{uid}"


def double(x: Meters) -> Meters:
    return x * 2


uid = UserId(7)
reveal_type(uid)  # UserId
reveal_type(uid + 1)  # int (arithmetic drops the NewType)
reveal_type(double(1.5))  # float
print(lookup(uid), double(2.0))
lookup(7)  # expect-error: int is not UserId (runs fine)
try:
    class Bad(UserId):  # expect-error: NewType cannot be subclassed
        pass
except TypeError as exc:
    print("runtime:", exc)
