# area: callables
# hypothesis: Two classes whose __call__ attributes are annotated with each other form a call cycle; the runtime call raises TypeError because the attributes hold no callable value.
# origin: runs/hits/d4v_callables_mutual_call_attr.py
# area: callables
# hypothesis: Two classes whose __call__ attributes are annotated with each other form a call cycle; the runtime call raises TypeError because the attributes hold no callable value.
from typing import ClassVar


class A:
    __call__: "B"


class B:
    __call__: "A"


class SubB(B):
    pass


class Cv:
    __call__: ClassVar["Cv"]


def call_a(a: A) -> str:
    try:
        a()  # expect-error
    except TypeError as exc:
        return "TypeError: " + str(exc)
    return "called"


def call_cv(c: Cv) -> str:
    try:
        c()  # expect-error
    except TypeError:
        return "TypeError"
    return "called"


print(call_a(A()))
print(call_a(SubB()))  # expect-error
print(call_cv(Cv()))
