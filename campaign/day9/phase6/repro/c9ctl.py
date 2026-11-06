from typing import reveal_type


class Tag[K: (int, str)]:
    def __init__(self, key: K) -> None:
        self.key = key


class Tag2[K: (int, str) = int]:
    key: K

    def __init__(self, key: K) -> None:
        self.key = key


class Tag3[K: object = int]:
    def __init__(self, key: K) -> None:
        self.key = key


t = Tag("a")
reveal_type(t.key)
t2 = Tag2("a")
reveal_type(t2.key)
t3 = Tag3("a")
reveal_type(t3.key)
