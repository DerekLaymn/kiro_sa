# area: descriptors_properties
# hypothesis: A plain class-body decorator without self, applied only to __delete__ of a data descriptor, runs under CPython and checkers must type the explicit __delete__ call.
# origin: runs/day10/parents/C_pyright_range/d5p_descriptors_decorated_get_pyright_rangeerror.py
# area: descriptors_properties
# hypothesis: A plain class-body decorator without self applied only to __delete__ of a data descriptor runs under CPython, and checkers must type the explicit __delete__ call.
from typing import reveal_type


class Slot:
    def logged(fn):
        return fn

    def __get__(self, obj: object, owner: type | None = None) -> int:
        return 7

    def __set__(self, obj: object, value: int) -> None:
        print('set', value)

    @logged
    def __delete__(self, obj: object) -> None:
        print('deleted')


class Holder:
    slot = Slot()


h = Holder()
reveal_type(h.slot)
h.slot = 5
print(h.slot)
del h.slot
Slot.__delete__(Slot(), h)
try:
    Slot.__delete__(Slot(), None, 1)  # expect-error
except TypeError:
    print('rejected')
