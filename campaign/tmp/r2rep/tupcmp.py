from typing import assert_type


def f(left: tuple[int, str], right: tuple[int, str]) -> None:
    assert_type(left < right, bool)


f((1, "a"), (2, "b"))
