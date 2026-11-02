def f(l: list[int | None]) -> None:
    # ty and pyright narrow through the aliased condition; mypy only narrows on the inline condition
    # (python/mypy#13807, an open feature request). A precision difference, not a bug in either checker.
    is_none = l[0] is None
    if is_none:
        reveal_type(l[0])
    else:
        reveal_type(l[0])
