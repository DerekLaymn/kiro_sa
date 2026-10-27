from typing import reveal_type


def f(x: int | str | float | bytes | list[int] | bool) -> str:
    match x:
        case bool(b):
            reveal_type(b)
            return "bool"
        case int(i):
            reveal_type(i)
            return "int"
        case str(s) | bytes(s):
            reveal_type(s)
            return "sb"
        case float(fl):
            reveal_type(fl)
            return "f"
        case list(l):
            reveal_type(l)
            return "l"
        case _:
            reveal_type(x)
            return "never"


def g(x: int | str) -> int:
    match x:
        case 0 | "":
            reveal_type(x)
            return 0
        case int() | str():
            reveal_type(x)
            return 1


print(f(True), f(1), f("a"), f(b"a"), f(1.5), f([1]), g(0), g(""), g(2))
