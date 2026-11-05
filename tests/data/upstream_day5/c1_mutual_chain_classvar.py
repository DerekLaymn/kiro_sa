# area: callables
# hypothesis: Classes whose __call__ attributes are annotated with each other, through a chain or a subclass, form a call cycle; the runtime call raises TypeError because the attributes are not callable.
# origin: runs/hits/d4v_callables_mutual_call_attr.py
# area: callables
# hypothesis: Classes whose __call__ attributes are annotated with each other, through a chain or a subclass, form a call cycle; the runtime call raises TypeError because the attributes are not callable.
from typing import ClassVar, Self


class A:
    __call__: "B"


class B:
    __call__: "A"


class SubB(B):
    pass


class Chain1:
    __call__: "Chain2"


class Chain2:
    __call__: "Chain3"


class Chain3:
    __call__: "Chain1"


class Cv:
    __call__: ClassVar["Cv"]


class Sx:
    __call__: Self


def call_a(a: A) -> str:
    try:
        a()  # expect-error
    except TypeError:
        return "TypeError"
    return "called"


def call_chain(c: Chain1) -> str:
    try:
        c()  # expect-error
    except TypeError:
        return "TypeError"
    return "called"


print(call_a(A()))
print(call_a(SubB()))  # expect-error
print(call_chain(Chain1()))
print(Cv.__name__, Sx.__name__)
