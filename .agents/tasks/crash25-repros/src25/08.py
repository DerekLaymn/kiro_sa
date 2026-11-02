# area: constructors_metaclasses
# origin: ruff mdtest call/constructor.md block 14
from collections.abc import Callable

def decorate[T](callback: Callable[[T], None]) -> T:
    raise NotImplementedError

class C:
    @decorate
    def __new__(cls):
        pass

reveal_type(C.__new__)  # revealed: type[C]
reveal_type(C())  # revealed: C
