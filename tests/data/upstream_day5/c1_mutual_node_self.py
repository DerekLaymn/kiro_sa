# area: callables
# hypothesis: Classes whose __call__ attributes are annotated with each other, or with a Self-typed chain, form a call cycle for checkers; the runtime call raises TypeError since no callable is stored.
# origin: runs/hits/d4v_callables_mutual_call_attr.py
# area: callables
# hypothesis: Classes whose __call__ attributes are annotated with each other, or with a Self-typed chain, form a call cycle for checkers; the runtime call raises TypeError since no callable is stored.
from typing import ClassVar, Self


class A:
    __call__: "B"


class B:
    __call__: "A"


class SubA(A):
    pass


class Node:
    __call__: "Node | None"


class Sx:
    __call__: Self


class Cv:
    __call__: ClassVar["Cv"]


def call_a(a: A) -> str:
    try:
        a()  # expect-error
    except TypeError:
        return "TypeError"
    return "called"


def call_node(n: Node) -> str:
    try:
        n()  # expect-error
    except TypeError:
        return "TypeError"
    return "called"


print(call_a(A()))
print(call_a(SubA()))  # expect-error
print(call_node(Node()))
print(Cv.__name__, Sx.__name__)
