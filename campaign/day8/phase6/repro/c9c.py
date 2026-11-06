from typing import reveal_type


def mk_closure():
    def inner(x: int) -> int:
        return x

    return inner


def mk_closure_capture(fn):
    def inner(x: int) -> int:
        return fn(x)

    return inner


def mk_lambda():
    return lambda x: x


def mk_int():
    return 1


reveal_type(mk_int())
reveal_type(mk_closure())
reveal_type(mk_closure_capture)
reveal_type(mk_closure_capture(len))
reveal_type(mk_lambda())
mk_closure()(1, 2)
