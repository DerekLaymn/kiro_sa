from typing import reveal_type


class K:
    def m(self, x: int) -> str:
        return "s"


def run(k: K) -> None:
    assert k.m(3) == 4
    reveal_type(k.m)
    reveal_type(k.m(1))
    reveal_type(k)
