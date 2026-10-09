# Reported to ty. Outcome: INTENDED. ty treats `Self` in a non-receiver parameter as a typevar bounded by
# Node and solves it per call, so x.add(Node()) is OK and returns Node (mypy/pyright bind Self to Leaf).
# The real ty bug is the displayed signature `bound method Leaf.add(c: Leaf) -> Leaf`: ty#4673.
# The later AttributeError comes from the mutable `list[Self]` attribute, which is unsound under any
# interpretation once a Leaf is used as a Node.
from typing import Self, reveal_type


class Node:
    def __init__(self) -> None:
        self.children: list[Self] = []

    def add(self, c: Self) -> Self:
        self.children.append(c)
        return self


class Leaf(Node):
    def leaf_only(self) -> int:
        return 1


x = Leaf()
reveal_type(x.add)
x.add(Node())
print(x.children[0].leaf_only())
