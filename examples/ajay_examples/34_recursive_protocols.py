# area: protocols
# explores: protocols using Self in a parameter, recursive protocol properties, bounded TypeVar on a protocol
from typing import Protocol, Self, reveal_type


class Comparable(Protocol):
    def __lt__(self, other: Self, /) -> bool: ...


class Linked(Protocol):
    @property
    def next(self) -> "Linked | None": ...


class Node:
    def __init__(self, value: int, nxt: "Node | None" = None) -> None:
        self.value = value
        self._next = nxt

    @property
    def next(self) -> "Node | None":
        return self._next


def biggest[T: Comparable](items: list[T]) -> T:
    best = items[0]
    for x in items[1:]:
        if best < x:
            best = x
    return best


def length(n: Linked | None) -> int:
    count = 0
    while n is not None:
        count += 1
        n = n.next
    return count


reveal_type(biggest([3, 1, 2]))  # int
reveal_type(biggest(["b", "a"]))  # str
print(biggest([3, 1, 2]), biggest(["b", "a"]), length(Node(1, Node(2))))
biggest([object()])  # expect-error: object has no __lt__ (one item, so runs fine)
