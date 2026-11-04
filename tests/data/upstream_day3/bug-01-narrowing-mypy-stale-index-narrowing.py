# Disagreement: after assigning to a narrowed index expression, mypy keeps the stale narrowed type; ty and pyright reset it.
# Faulty tool: mypy 2.4.0 -- reveals `int` for xs[0] after `xs[0] = None` and misses the runtime TypeError on the `+`.
# Reproduce (run in a dir without pyproject/ty.toml):
#   .venv/bin/mypy --python-version 3.13 --check-untyped-defs --show-error-codes --no-incremental <this file>
#   .venv/bin/ty check --python-version 3.13 --output-format concise <this file>
#   .venv/bin/pyright --pythonversion 3.13 <this file>
#   .venv/bin/python <this file>        # TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'
from typing import reveal_type


def a(xs: list[int | None]) -> int:
    if xs[0] is not None:
        xs[0] = None
        reveal_type(xs[0])
        return xs[0] + 1
    return 0


a([1])
