# Disagreement: ty infers `Literal[F.R, F.W]` for `F.R | F.W` on an enum.Flag; mypy and pyright infer `F`.
# Faulty tool: ty 0.0.84 -- the runtime value <F.R|W: 3> is neither member; the typing spec exempts Flag from literal expansion.
# Reproduce:
#   .venv/bin/mypy --python-version 3.13 --check-untyped-defs --show-error-codes --no-incremental <this file>
#   .venv/bin/ty check --python-version 3.13 --output-format concise <this file>
#   .venv/bin/pyright --pythonversion 3.13 <this file>
#   .venv/bin/python <this file>        # prints <F.R|W: 3> False False
import enum
from typing import reveal_type


class F(enum.Flag):
    R = 1
    W = 2


a = F.R | F.W
reveal_type(a)
print(repr(a), a is F.R, a is F.W)
