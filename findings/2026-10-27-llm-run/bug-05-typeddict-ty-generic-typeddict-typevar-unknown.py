# Disagreement: ty cannot solve T from a generic TypedDict argument (Unknown); mypy and pyright solve it (int/str) and report the mismatches.
# Faulty tool: ty 0.0.84 -- first(a) is `Unknown`, so the two bad assignments below are silently accepted.
# Reproduce:
#   .venv/bin/mypy --python-version 3.13 --check-untyped-defs --show-error-codes --no-incremental <this file>
#   .venv/bin/ty check --python-version 3.13 --output-format concise <this file>
#   .venv/bin/pyright --pythonversion 3.13 <this file>
#   .venv/bin/python <this file>        # runs fine
from typing import Generic, TypedDict, TypeVar, reveal_type

T = TypeVar("T")


class Resp(TypedDict, Generic[T]):
    data: T
    errors: list[str]


def first(r: Resp[T]) -> T:
    return r["data"]


def go(a: Resp[int], c: Resp[str]) -> None:
    reveal_type(first(a))
    x: int = first(c)  # expected error
    y: str = first(a)  # expected error


go({"data": 1, "errors": []}, {"data": "s", "errors": []})
