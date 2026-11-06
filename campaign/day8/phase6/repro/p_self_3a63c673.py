# area: self_classmethods
# hypothesis: Self in a parameter of an inherited method must bind to the subclass, so passing a base-class Node where a Leaf is expected should be rejected.
# origin: runs/day8/parents/N_seeds_b/self_classmethods__self_param_inherited.py
# area: self_classmethods
# hypothesis: Self in a parameter of an inherited method must bind to the subclass.
# spec: typing spec, Self in non-receiver parameters is ambiguous; checkers may disagree.
from typing import Self, reveal_type


class Node:
    def add(self, c: 'Self') -> 'Self':
        return self


class Leaf(Node):
    pass


x = Leaf()
reveal_type(x.add)
x.add(Node())  # expect-error: Node is not a Leaf (mypy and pyright report this)
x.add(c=Node())  # expect-error: keyword form
Leaf.add(Leaf(), Node())  # expect-error: unbound form
print('done')
