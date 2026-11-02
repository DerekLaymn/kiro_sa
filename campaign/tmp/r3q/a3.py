class C:
    pass


def g(c: C) -> None:
    reveal_type(c.x + 1)
