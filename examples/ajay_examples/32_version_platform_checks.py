# area: narrowing_builtin (reachability)
# explores: sys.version_info / sys.platform branches, TYPE_CHECKING-only imports, unreachable imports
import sys
from typing import TYPE_CHECKING, reveal_type

if TYPE_CHECKING:
    from collections.abc import Sequence

if sys.version_info >= (3, 13):
    def newest() -> str:
        return "3.13+"
else:
    def newest() -> int:
        return 0

if sys.platform == "win32":
    SEP = "\\"
else:
    SEP = "/"


def total(xs: "Sequence[int]") -> int:
    return sum(xs)


reveal_type(newest())  # str for --python-version 3.13
reveal_type(SEP)  # depends on --python-platform
print(newest(), SEP, total([1, 2]))
if sys.version_info < (3, 10):
    import module_that_does_not_exist  # unreachable for the target version: no error expected
