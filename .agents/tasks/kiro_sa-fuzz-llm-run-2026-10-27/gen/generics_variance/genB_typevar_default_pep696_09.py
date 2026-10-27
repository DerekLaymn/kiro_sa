from typing import reveal_type


class Pair[K, V = int]:
    def __init__(self, k: K, v: V) -> None:
        self.k = k
        self.v = v


p: Pair[str] = Pair("a", 1)
reveal_type(p)
reveal_type(p.v)
q = Pair("a", "b")
reveal_type(q)
r: Pair[str] = Pair("a", "b")  # error: V is int
print(p.v, q.v, r.v)
