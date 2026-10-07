# area: narrowing_user
# explores: TypeGuard may narrow to a non-subtype (list[object] -> list[str]); TypeIs may not; methods as guards
from typing import TypeGuard, TypeIs, reveal_type


def all_str(xs: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(x, str) for x in xs)


def is_str_list(xs: list[object]) -> TypeIs[list[str]]:  # expect-error: list[str] is not a subtype of list[object]
    return all(isinstance(x, str) for x in xs)


def join(xs: list[object]) -> str:
    if all_str(xs):
        reveal_type(xs)  # list[str]
        return ",".join(xs)
    reveal_type(xs)  # list[object]
    return "mixed"


class Validator:
    def is_positive(self, n: int | str) -> TypeGuard[int]:
        return isinstance(n, int) and n > 0


def check(v: Validator, n: int | str) -> str:
    if v.is_positive(n):
        reveal_type(n)  # int
        return "pos"
    return "no"


print(join(["a", "b"]), join([1, "a"]), is_str_list(["a"]), check(Validator(), 3), check(Validator(), "x"))
