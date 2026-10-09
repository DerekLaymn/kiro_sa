# The case that TAUGHT typediff its Self rules (reported as ty#4656; the maintainers' verdict: INTENDED).
# ty treats `Self` in a non-receiver parameter as a TypeVar bounded by Node and solves it jointly with the
# receiver, so x.add(Node()) is accepted (Self = Node); mypy and pyright pin Self to Leaf and reject it.
# The typing spec is ambiguous. The printed `bound method Leaf.add(c: Leaf)` is a display bug (ty#4673).
# The AttributeError needs the Self-typed `children` attribute (PEP 673's LinkedList.next pattern): there ty
# IS unsound (ty#2255). Expected typediff result: REVIEW only, weak SELF_CONTRADICTION, KB hint demoted.
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
