from typing import Self, reveal_type


class Node:
    def add(self, c: "Self") -> "Self":
        return self


class Leaf(Node):
    pass


x = Leaf()
reveal_type(x.add)
x.add(Node())
