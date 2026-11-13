class C:
    __call__: "C"

def f(x: C) -> None:
    x()
