from typing import reveal_type


class B:
    v: int | None = 1


def attr_control(b: B) -> None:
    if b.v is not None:
        b.v = None
        reveal_type(b.v)  # mypy resets on attribute assignment


def list_idx(xs: list[int | None]) -> None:
    if xs[0] is not None:
        xs[0] = None
        reveal_type(xs[0])  # mypy keeps stale `int`


def dict_key(d: dict[str, int | None]) -> None:
    if d["k"] is not None:
        d["k"] = None
        reveal_type(d["k"])


def isinstance_form(t: list[int | str]) -> None:
    assert isinstance(t[0], int)
    t[0] = "coucou"  # same shape as python/mypy#20969
    reveal_type(t[0])


def del_form(xs: list[int | None]) -> None:
    if xs[0] is not None:
        del xs[0]
        reveal_type(xs[0])


def var_index(xs: list[int | None], i: int) -> None:
    if xs[i] is not None:  # mypy never narrows non-literal indices
        xs[i] = None
        reveal_type(xs[i])
