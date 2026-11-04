# Reviewer-minimised witness for bug-02 (assert_type is spec-defined, so no reveal_type text comparison is needed).
# Disagreement: ty rejects assert_type(F.R | F.W, F); mypy and pyright accept it. The runtime value is <F.R|W: 3>.
# Reproduce (run in a dir without pyproject/ty.toml):
#   .venv/bin/mypy --python-version 3.13 --check-untyped-defs --show-error-codes --no-incremental <this file>
#   .venv/bin/ty check --python-version 3.13 --output-format concise <this file>
#   .venv/bin/pyright --pythonversion 3.13 <this file>
#   .venv/bin/python <this file>        # <F.R|W: 3> False False
import enum
from typing import assert_type


class F(enum.Flag):
    R = 1
    W = 2


v = F.R | F.W
assert_type(v, F)
print(repr(v), v is F.R, v is F.W)
