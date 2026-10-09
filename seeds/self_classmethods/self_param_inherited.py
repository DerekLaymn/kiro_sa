# area: self_classmethods
# status: REPORTED as ty#4656 -> INTENDED (not a bug). Kept as the regression seed for typediff's Self rules.
# ty treats `Self` in a non-receiver parameter as a TypeVar bounded by Node, solved jointly with the receiver
# (Self = Node here); mypy/pyright pin it to the receiver (Leaf). The typing spec is ambiguous. The printed
# `bound method Leaf.add(c: Leaf)` is a display bug: ty#4673. See ty#1172 (earlier discussion), ty#2255.
# hypothesis (original, refuted): `Self` in a parameter of an inherited method must bind to the subclass.
from typing import Self, reveal_type


class Node:
    def add(self, c: Self) -> Self:
        return self


class Leaf(Node):
    pass


x = Leaf()
reveal_type(x.add)
x.add(Node())  # expect-error: Node is not a Leaf (mypy and pyright report this)
x.add(c=Node())  # expect-error: keyword form
Leaf.add(Leaf(), Node())  # expect-error: unbound form
print("done")
