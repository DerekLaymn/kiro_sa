# area: self_classmethods
# explores: Self in dataclass fields and methods (incl. dataclasses.replace), Self-returning protocols
from dataclasses import dataclass, field, replace
from typing import Protocol, Self, reveal_type


@dataclass
class TreeNode:
    name: str
    children: list[Self] = field(default_factory=list)

    def add(self, child: Self) -> Self:
        self.children.append(child)
        return self

    def renamed(self, name: str) -> Self:
        return replace(self, name=name)


@dataclass
class TaggedNode(TreeNode):
    tag: str = ""


class Cloneable(Protocol):
    def clone(self) -> Self: ...


class Sheep:
    def clone(self) -> Self:
        return type(self)()


def twin[C: Cloneable](x: C) -> tuple[C, C]:
    return x, x.clone()


t = TaggedNode("root", tag="r").add(TaggedNode("leaf"))
reveal_type(t)  # TaggedNode
reveal_type(t.children)  # list[TaggedNode]
reveal_type(t.renamed("x"))  # TaggedNode
reveal_type(twin(Sheep()))  # tuple[Sheep, Sheep]
print(t.renamed("x").name, len(t.children), twin(Sheep()))
TaggedNode("a").add(TreeNode("b"))  # expect-error: TreeNode is not a TaggedNode
