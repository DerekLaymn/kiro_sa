import sys
from mypy.main import main
import mypy.checkexpr as ce

orig = ce.covers_at_runtime


def wrapped(item, supertype):
    r = orig(item, supertype)
    if type(item).__name__ == "TupleType":
        return r
    print(f"covers_at_runtime({type(item).__name__}: {item}, {type(supertype).__name__}: {supertype}) -> {r}")
    return r


ce.covers_at_runtime = wrapped
try:
    main(args=["--python-version", "3.13", "--no-incremental", "--no-error-summary", sys.argv[1]], stdout=sys.stdout, stderr=sys.stderr, clean_exit=True)
except SystemExit:
    pass
