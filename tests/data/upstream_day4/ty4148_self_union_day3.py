# area: self_classmethods
# hypothesis: A Self-typed __call__ method returns the subclass instance at runtime, while a None-valued __call__ attribute raises TypeError.
# origin: generated program of the campaign (not kept)
# area: self_classmethods
# hypothesis: a Self-typed __call__ method returns the subclass instance at runtime, and a None-valued __call__ attribute raises TypeError.
from typing import Self


class Node:
    def __call__(self) -> Self:
        return self


class Leaf(Node):
    pass


leaf = Leaf()
assert leaf() is leaf
assert isinstance(leaf(), Leaf)


class Broken:
    __call__: Self | None = None


failed = False
try:
    Broken()()  # expect-error
except TypeError:
    failed = True
assert failed
