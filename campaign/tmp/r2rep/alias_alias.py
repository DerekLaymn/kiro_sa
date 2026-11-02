def f(x: int | None) -> None:
    is_none = x is None
    if is_none:
        reveal_type(x)
    else:
        reveal_type(x)


def g(x: int | None) -> None:
    if x is None:
        reveal_type(x)
    else:
        reveal_type(x)


f(None)
g(None)
