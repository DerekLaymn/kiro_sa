from typing import reveal_type


class A:
    pass


def f(v: A | str) -> str:
    if type(v) == str:
        reveal_type(v)
        return "str"
    return "other"


def g(v: A | str, sample: str) -> str:
    if type(v) == type(sample):
        reveal_type(v)
        return "same"
    return "other"
