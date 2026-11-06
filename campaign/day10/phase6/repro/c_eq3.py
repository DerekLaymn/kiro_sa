from typing import reveal_type


class M(type):
    def __eq__(cls, other: object) -> bool:
        return True

    def __hash__(cls) -> int:
        return 0


class A(metaclass=M):
    pass


def g(v: A | str, sample: str) -> str:
    if type(v) == type(sample):
        reveal_type(v)
        return "same"
    return "other"


def h(v: A | str) -> str:
    if type(v) is str:
        reveal_type(v)
        return "str"
    return "other"


print(g(A(), "q"))
