# area: callables
# hypothesis: A class whose __call__ is only a recursively aliased Callable attribute should be rejected when its instances are called, and CPython raises TypeError, so checkers that accept the call are unsound.
# origin: runs/day8/parents/A_ty_escape/d3p_callables_self_call_attr.py
# area: callables
# hypothesis: A class whose __call__ is only a recursively aliased Callable attribute should be rejected when instances are called, and CPython raises TypeError, so checkers that accept the call are unsound.
from collections.abc import Callable


type Step = Callable[[], Step | None]


class C:
    __call__: Step  # declared attribute only, no __call__ method

    def run(self) -> str:
        return 'ran'


def probe() -> str:
    c = C()
    try:
        c()  # expect-error: C instances are not callable
    except TypeError:
        return 'TypeError'
    return 'called'


print(C().run())
print(probe())
