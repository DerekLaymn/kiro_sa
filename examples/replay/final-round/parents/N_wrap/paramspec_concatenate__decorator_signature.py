# area: paramspec_concatenate
# hypothesis: decorators using ParamSpec + Concatenate must preserve and check the remaining signature,
# including on methods (where `self` is the first bound parameter).
from collections.abc import Callable
from typing import Concatenate, reveal_type


def logged[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    def inner(*args: P.args, **kwargs: P.kwargs) -> R:
        return fn(*args, **kwargs)
    return inner


def with_db[**P, R](fn: Callable[Concatenate[str, P], R]) -> Callable[P, R]:
    def inner(*args: P.args, **kwargs: P.kwargs) -> R:
        return fn("db", *args, **kwargs)
    return inner


@logged
def scale(x: int, *, by: int = 2) -> int:
    return x * by


@with_db
def query(db: str, table: str, limit: int = 10) -> list[str]:
    return [f"{db}.{table}"] * limit


class Repo:
    @logged
    def find(self, key: str) -> int:
        return len(key)


reveal_type(scale)
reveal_type(query)
reveal_type(Repo().find)
print(scale(3, by=4), query("t", limit=1), Repo().find("k"))
scale("3")  # expect-error
try:
    query("t", 1, 2)  # expect-error: too many positional arguments
except TypeError as exc:
    print('runtime:', type(exc).__name__)
try:
    Repo().find(1)  # expect-error
except TypeError as exc:
    print('runtime:', type(exc).__name__)
