# Added by the final reviewer (not in candidates.md). Re-derived from the bug-02 Flag probes.
# Disagreement: mypy expands enum.Flag into the union of its members for `is` narrowing, so the `else` branch is
# treated as unreachable and never checked; ty and pyright keep `F` and report the error.
# Faulty tool: mypy 2.4.0 -- misses `1 + "bad"`, which runs: h(F.R | F.W) is neither F.R nor F.W.
# Spec (enums, Enum Literal Expansion): "This rule does not apply to classes that derive from enum.Flag
# because these enums allow flags to be combined in arbitrary ways."
# Reproduce (run in a dir without pyproject/ty.toml):
#   .venv/bin/mypy --python-version 3.13 --check-untyped-defs --show-error-codes --no-incremental <this file>
#   .venv/bin/ty check --python-version 3.13 --output-format concise <this file>
#   .venv/bin/pyright --pythonversion 3.13 <this file>
#   .venv/bin/python <this file>        # TypeError: unsupported operand type(s) for +: 'int' and 'str'
import enum


class F(enum.Flag):
    R = 1
    W = 2


def h(x: F) -> str:
    if x is F.R:
        return "R"
    elif x is F.W:
        return "W"
    else:
        return 1 + "bad"


print(h(F.R | F.W))
