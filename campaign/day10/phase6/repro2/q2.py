from typing import Callable, reveal_type


def run(g: Callable[[int], str]) -> None:
    assert g(3) == 4
    reveal_type(g)
    reveal_type(g(1))
