from typing import Generic, TypeVar, reveal_type

K = TypeVar("K", int, str)


class Old(Generic[K]):
    def __init__(self, key: K) -> None:
        self.key = key


class Plain[K2: (int, str)]:
    def __init__(self, key: K2) -> None:
        self.key = key

    def get(self) -> K2:
        return self.key


class Bound[B: float]:
    def __init__(self, key: B) -> None:
        self.key = key


reveal_type(Old("a").key)
reveal_type(Plain("a").key)
reveal_type(Bound(1.5).key)
