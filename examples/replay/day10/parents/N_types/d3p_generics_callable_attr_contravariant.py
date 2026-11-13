# area: generics_variance
# hypothesis: A PEP 695 generic class stores a Callable[[T], None]; mypy accepts Handler[float] where Handler[int] is expected and the call fails at runtime. Vary: store the callback in a list/dict/tuple, use a property setter, use a Protocol with __call__, change the parameter to Callable[[T], T].
# origin: project/temp/mypy_callable_variance.py (team-filed mypy variance report)
from typing import Callable


class Handler[T]:
    def __init__(self, cb: Callable[[T], None]) -> None:
        self.cb = cb


def use(h: Handler[int]) -> None:
    h.cb = lambda v: print(v.bit_length())


hf = Handler[float](lambda x: print(x.is_integer()))
use(hf)  # mypy should reject this
hf.cb(1.5)  # runtime: AttributeError, 'float' has no attribute 'bit_length'
