from typing import reveal_type


def g(x: int) -> str:
    return "s"


def run() -> str:
    assert g(3) == 4
    return g(1)


def run2() -> int:
    assert g(3) == 4
    return len(g(1))


print(run2)
