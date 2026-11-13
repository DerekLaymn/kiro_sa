# area: callables
# hypothesis: two classes whose __call__ is an attribute annotated with the other class form a call cycle; ty overflows its stack and compiled mypy segfaults when an instance is called (same root cause as the one-class case ty#4148 and mypy#22361), pyright accepts it, CPython raises TypeError if called. Vary: ClassVar["C"], Self, "C | None", a subclass instance, a chain of three classes.
# origin: d4v-v1 verify of round3 seeds 0032056ba741 and 3e7d6fb5688c (self_call_attr family); variant of ty#4148, mypy#22361
class A:
    __call__: "B"


class B:
    __call__: "A"


def call(a: A) -> None:
    a()
