# area: dunder_dispatch
# hypothesis: A class whose __call__ exists only as an annotation (`__call__: Step`, no definition) must be rejected when an instance is called, and CPython raises TypeError because special methods are looked up on the type, so a checker that accepts `C()()` is unsound. Vary: the protocol (iter, len, getitem, enter, contains), an instance assignment `self.__call__ = fn`, a metaclass-level definition, an inherited definition as control.
# origin: generated mutant of d3p_callables_self_call_attr (not kept); ty and pyright accept the call, mypy rejects it for another reason
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
