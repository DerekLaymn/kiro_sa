# Disagreement: mypy reports `attr-defined` for class access of an InitVar field that has a default; ty reveals `int`.
# Faulty tool: mypy 2.4.0 -- false positive, valid code (dataclasses leaves the default as a class attribute).
# Reproduce:
#   .venv/bin/mypy --python-version 3.13 --check-untyped-defs --show-error-codes --no-incremental <this file>
#   .venv/bin/ty check --python-version 3.13 --output-format concise <this file>
#   .venv/bin/pyright --pythonversion 3.13 <this file>
#   .venv/bin/python <this file>        # prints 0
from dataclasses import InitVar, dataclass
from typing import reveal_type


@dataclass
class Sub:
    extra: InitVar[int] = 0


reveal_type(Sub.extra)
print(Sub.extra)
