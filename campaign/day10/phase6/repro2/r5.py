from typing import reveal_type


def name(n: int) -> str:
    return str(n)


def run(n: int, m: int) -> None:
    assert name(n) + name(m) == 4
    reveal_type(n)
    reveal_type(m)


def run2(n: int, m: int) -> None:
    assert name(n * 2) == 4
    reveal_type(n)
    reveal_type(name)
