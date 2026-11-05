# area: callables
# hypothesis: A __call__ that is only an annotation leaves the instance uncallable, so calling it raises TypeError; the call is wrapped so the witness is recorded.
# origin: runs/hits/d3p_callables_self_call_attr.py
# area: callables
# hypothesis: a class whose __call__ is only an annotation has no callable at runtime, so calling its instance raises TypeError.
class C:
    __call__: "C"


class Adder:
    def __call__(self, n: int) -> int:
        return n + 1


assert Adder()(1) == 2
failed = False
try:
    C()()  # expect-error
except TypeError:
    failed = True
assert failed
