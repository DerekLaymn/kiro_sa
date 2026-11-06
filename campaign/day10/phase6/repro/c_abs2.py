class Node:
    parent: Node | None = None

    def link(self, other: Node) -> None:
        self.parent = other


print(Node())
