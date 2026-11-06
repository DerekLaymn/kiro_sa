# area: descriptors_properties
# hypothesis: After contradictory attribute asserts and a __dict__ write, assigning to a read-only property inside a function raises AttributeError, while checkers may infer the receiver as Never and skip that line.
# origin: runs/day8/parents/P_pyright/d4p_descriptors_readonly_prop_never.py
# area: descriptors_properties
# hypothesis: After contradictory attribute asserts and a __dict__ write, assigning to a read-only property inside a function raises AttributeError; checkers may infer the receiver as Never and skip the line.
from typing import reveal_type


class Doubled:
    def __get__(self, obj: object | None, objtype: type | None = None) -> int:
        if obj is None:
            return -1
        return getattr(obj, 'base') * 2


class Thing:
    doubled = Doubled()

    def __init__(self, base: int) -> None:
        self.base = base

    def bump(self) -> None:
        self.base += 1

    @property
    def readonly(self) -> int:
        return self.base


def probe(t: Thing) -> bool:
    assert Thing.doubled == -1
    assert t.doubled == 8
    t.__dict__['doubled'] = 99
    assert t.doubled == 99
    t.bump()
    assert t.readonly == 5
    reveal_type(t.readonly)
    n = 7
    try:
        t.readonly = n  # expect-error
    except AttributeError:
        return True
    return False


print(probe(Thing(4)))
