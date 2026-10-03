# area: final_classvar
# hypothesis: Final names/attributes cannot be reassigned or overridden; @final methods/classes cannot be
# overridden/subclassed; ClassVar cannot be assigned through an instance.
# spec: typing spec, qualifiers.html.
from typing import ClassVar, Final, final


class Base:
    LIMIT: Final = 10
    counter: ClassVar[int] = 0

    def __init__(self) -> None:
        self.ident: Final[str] = "base"

    @final
    def locked(self) -> int:
        return 1


class Child(Base):
    LIMIT = 20  # expect-error: cannot override Final

    def locked(self) -> int:  # expect-error: cannot override @final
        return 2


@final
class Leaf:
    pass


class SubLeaf(Leaf):  # expect-error: cannot subclass @final class
    pass


b = Base()
b.ident = "x"  # expect-error: Final attribute
b.counter = 1  # expect-error: ClassVar assigned via instance
print(Child().LIMIT, Child().locked(), b.counter)
