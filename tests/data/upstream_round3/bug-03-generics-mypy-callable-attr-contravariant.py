# Disagreement: mypy infers PEP 695 `Handler[T]` (mutable Callable[[T], None] attribute) as contravariant; ty and pyright say invariant.
# Faulty tool: mypy 2.4.0 -- accepts Handler[float] as Handler[int] (no error); the runtime then raises AttributeError.
# Reproduce:
#   .venv/bin/mypy --python-version 3.13 --check-untyped-defs --show-error-codes --no-incremental <this file>
#   .venv/bin/ty check --python-version 3.13 --output-format concise <this file>
#   .venv/bin/pyright --pythonversion 3.13 <this file>
#   .venv/bin/python <this file>        # AttributeError: 'float' object has no attribute 'bit_length'
from collections.abc import Callable


class Handler[T]:
    def __init__(self, cb: Callable[[T], None]) -> None:
        self.cb = cb


def use(h: Handler[int]) -> None:
    h.cb = lambda v: print(v.bit_length())


hf = Handler[float](lambda x: print(x.is_integer()))
use(hf)
hf.cb(1.5)
