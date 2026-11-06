# area: descriptors_properties
# hypothesis: After a method bump and a __dict__ write, assigning to a read-only property must raise AttributeError, which ty may skip if it infers the receiver as Never.
# origin: runs/day8/parents/P_pyright/d4p_descriptors_readonly_prop_never.py
# area: descriptors_properties
# hypothesis: After a method bump and a __dict__ write, assigning to a read-only property must raise AttributeError, which ty may skip if it infers the receiver as Never.
from typing import reveal_type


class Counter:
    def __init__(self, start: int) -> None:
        self.base = start

    def bump(self) -> None:
        self.base += 1

    @property
    def readonly(self) -> int:
        return self.base


def poke(c: Counter, value: int) -> None:
    c.__dict__['base'] = value
    c.bump()


c = Counter(4)
assert c.base == 4
c.bump()
assert c.base == 5
poke(c, 10)
assert c.base == 11
reveal_type(c.readonly)
assert c.readonly == 11


def try_write(c: Counter) -> bool:
    try:
        c.readonly = 0  # expect-error
    except AttributeError:
        return True
    return False


assert try_write(c)
print('done')
