# Reviewer-minimised witness for bug-05, with a runtime crash that ty does not predict.
# Disagreement: ty solves T to Unknown from a Resp[int] argument and accepts `y: str = first(a)`;
# mypy and pyright report the assignment. CPython raises AttributeError on y.upper().
# Reproduce (run in a dir without pyproject/ty.toml):
#   .venv/bin/mypy --python-version 3.13 --check-untyped-defs --show-error-codes --no-incremental <this file>
#   .venv/bin/ty check --python-version 3.13 --output-format concise <this file>
#   .venv/bin/pyright --pythonversion 3.13 <this file>
#   .venv/bin/python <this file>        # AttributeError: 'int' object has no attribute 'upper'
from typing import Generic, TypedDict, TypeVar

T = TypeVar("T")


class Resp(TypedDict, Generic[T]):
    data: T


def first(r: Resp[T]) -> T:
    return r["data"]


a: Resp[int] = {"data": 1}
y: str = first(a)
print(y.upper())
