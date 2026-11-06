# area: descriptors_properties
# hypothesis: A class-body decorator without self that returns its argument, applied to __get__, should leave descriptor lookup on the class and on instances unchanged, so both checkers and CPython should agree that the result is 42.
# origin: runs/day8/parents/P_pyright/d3p_descriptors_decorated_get.py
# area: descriptors_properties
# hypothesis: A class-body decorator without self that returns its argument, applied to __get__, leaves the descriptor usable at runtime so access through the class and through instances yields 42.
from typing import reveal_type


class C:
    def deco(fn):
        return fn

    @deco
    def __get__(self, obj: object, owner: type | None = None) -> int:
        return 42


class Host:
    attr = C()


reveal_type(C.__get__)
assert C.__get__(C(), None, C) == 42
print(C.__get__(C(), None, C))
print(Host.attr)
print(Host().attr)
