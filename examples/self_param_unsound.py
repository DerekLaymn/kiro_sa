# Hypothesis: when `Self` appears in a *parameter* of a method, binding through a subclass instance
# must specialise it (x.add expects Leaf). ty 0.0.84 reveals `bound method Leaf.add(c: Leaf) -> Leaf`
# yet accepts x.add(Node()); mypy and pyright reject it, and CPython fails later.
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
