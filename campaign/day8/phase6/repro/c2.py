from typing import reveal_type


class Counter:
    def __init__(self, start: int) -> None:
        self.base = start

    def bump(self) -> None:
        self.base += 1

    @property
    def readonly(self) -> int:
        return self.base


c = Counter(4)
assert c.base == 4
c.bump()
assert c.base == 5
reveal_type(c.readonly)
