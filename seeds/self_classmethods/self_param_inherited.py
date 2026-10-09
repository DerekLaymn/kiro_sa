# area: self_classmethods
# status: REPORTED -> INTENDED in ty: Self in a parameter is a typevar bounded by Node and solved per call
#         (Self=Node here). The displayed signature `bound method Leaf.add(c: Leaf)` is the real bug: ty#4673
# hypothesis: `Self` in a parameter of an inherited (not overridden) method must bind to the subclass.
# spec: typing spec - `Self` behaves like a TypeVar bounded by the enclosing class. mypy/pyright bind it to the
# receiver (Leaf); ty solves it from all arguments (Node). Both readings exist; ty's preserves Liskov substitutability.
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
