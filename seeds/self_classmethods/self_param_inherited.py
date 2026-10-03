# area: self_classmethods
# status: REFERENCE BUG (ty 0.0.84 false negative, found by typediff) - keep as a regression seed
# hypothesis: `Self` in a parameter of an inherited (not overridden) method must bind to the subclass.
# spec: PEP 673 - `Self` is bound to the type of the receiver; Leaf().add expects a Leaf.
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
