# area: descriptors_properties
# hypothesis: A read-only property assignment after contradictory attribute asserts and a __dict__ write: ty infers the receiver as Never and skips the AttributeError line; mypy and pyright report it. Vary: bump through a method, a descriptor, a local int.
# origin: runs/day3/gen/descriptors_properties/gen7_14eb1842.py (seed-4aa8be0814f0); results/days/day3-report.md section 5 item 1
class Doubled:
    def __get__(self, obj: object | None, objtype: type | None = None) -> int:
        if obj is None:
            return -1
        return getattr(obj, "base") * 2


class Thing:
    doubled = Doubled()

    def __init__(self, base: int) -> None:
        self.base = base

    @property
    def readonly(self) -> int:
        return self.base


t = Thing(4)
assert Thing.doubled == -1
assert t.doubled == 8
t.__dict__["doubled"] = 99
assert t.doubled == 99
assert t.readonly == 4
failed = False
try:
    t.readonly = 5  # expect-error
except AttributeError:
    failed = True
assert failed
