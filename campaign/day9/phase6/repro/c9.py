from typing import reveal_type


class Tag[K: (int, str) = int]:
    def __init__(self, key: K) -> None:
        self.key = key


t = Tag("a")
reveal_type(t)
reveal_type(t.key)
print(t.key)
