# area: descriptors_properties
# hypothesis: A read-only property wrapped by a decorator still rejects assignment with AttributeError after a data descriptor bumps the underlying value; checkers should flag the same assignment line.
# origin: runs/day7/parents/P_pyright/d4p_descriptors_readonly_prop_never.py
# area: descriptors_properties
# hypothesis: A read-only property wrapped by a decorator still rejects assignment with AttributeError after a data descriptor bumps the underlying value; checkers should flag the same assignment line.
from collections.abc import Callable
from functools import wraps
from typing import reveal_type


def logged[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    @wraps(fn)
    def inner(*args: P.args, **kwargs: P.kwargs) -> R:
        return fn(*args, **kwargs)

    return inner


class Bumper:
    def __set__(self, obj: "Thing", value: int) -> None:
        obj.base += value


class Thing:
    bumped = Bumper()

    def __init__(self, base: int) -> None:
        self.base = base

    @property
    @logged
    def readonly(self) -> int:
        return self.base


t = Thing(4)
t.__dict__["base"] = 4
assert t.base == 4
t.bumped = 3
reveal_type(t.readonly)
assert t.base == 7
assert t.readonly == 7
failed = False
try:
    t.readonly = 5  # expect-error
except AttributeError:
    failed = True
assert failed
