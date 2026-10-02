def f(x: int) -> None:
    print(x)


f("b")  # type: ignore[arg-type]
f("c")  # type: ignore[ty:invalid-argument-type]
