from typing import reveal_type


def mixed(n: int) -> int | str:
    return n


def anything(n: int) -> object:
    return n


def run(n: int) -> None:
    assert mixed(n) == 4
    reveal_type(n)
    reveal_type(mixed)


def run2(n: int) -> None:
    assert anything(n) == 4
    reveal_type(n)
    reveal_type(anything)
