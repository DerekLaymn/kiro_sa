def cond(flag: bool) -> None:
    if flag:
        def f(x: int) -> int:
            return x
    f(1)


cond(False)
