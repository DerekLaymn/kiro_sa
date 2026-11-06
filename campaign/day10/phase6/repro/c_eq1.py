from typing import reveal_type


class M(type):
    def __eq__(cls, other: object) -> bool:
        return True

    def __hash__(cls) -> int:
        return 0


class A(metaclass=M):
    pass


def f(v: A | str) -> str:
    if type(v) == str:
        reveal_type(v)
        return "str"
    return "other"


print(f(A()))
