# area: generics_variance
# hypothesis: PEP 696 TypeVar defaults apply when a generic is used unparameterised or partially.
# spec: typing spec, generics.html "Defaults for type parameters".
from typing import reveal_type


class Pair[K, V = K]:
    def __init__(self, k: K, v: V) -> None:
        self.k, self.v = k, v


class Wrapper[T = int]:
    def __init__(self, item: T | None = None) -> None:
        self.item = item


def first(p: Pair[str]) -> str:
    reveal_type(p.v)  # spec: str (default = K)
    return p.k


w = Wrapper()
reveal_type(w)  # spec: Wrapper[int]
print(first(Pair("a", "b")), w.item)
