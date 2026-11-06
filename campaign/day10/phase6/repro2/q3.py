from typing import reveal_type


def g(x: int) -> str:
    return "s"


def a() -> None:
    assert g(3) == 4.5
    reveal_type(g)


def b() -> None:
    assert g(3) == True
    reveal_type(g)


def c() -> None:
    assert g(3) == None
    reveal_type(g)


def d() -> None:
    assert g(3) == "s"
    reveal_type(g)


def e() -> None:
    assert g(3) != 4
    reveal_type(g)


def f() -> None:
    assert g(3) == b"s"
    reveal_type(g)


def h() -> None:
    assert g(3) == 4_000
    reveal_type(g)


def i() -> None:
    assert 4 == g(3)
    reveal_type(g)
