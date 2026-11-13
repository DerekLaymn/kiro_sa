"""Round 10 phase 5: KB entry ``MYPY-8595-METACLASS-CALL`` (matcher ``m_metaclass_call_return``).

mypy ignores the return annotation of a metaclass ``__call__`` (python/mypy#8595, closed, "unlikely this will be ever
supported"); ty, pyright and CPython use it. Seen on Round 9 (1 live finding) and Round 10 (4 live findings in 2 programs).
Every positive has near-miss controls that must stay live."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from typediff.kb import BY_ID, matching_entries
from typediff.models import Diagnostic, Discrepancy, DiscrepancyKind as K, RuntimeResult, Severity, Tool
from typediff.state import CaseState

BIN = Path(sys.executable).parent
needs_tools = pytest.mark.skipif(
    not all((BIN / t).exists() for t in ("mypy", "ty", "pyright")), reason="mypy/ty/pyright not installed")

EID = "MYPY-8595-METACLASS-CALL"

SRC = '''\
from typing import Any, Self, TypeVar, assert_type, reveal_type

T = TypeVar("T")


class Meta(type):
    def __call__(cls, value: int) -> str:
        return "wrapped:" + str(value)


class Box(metaclass=Meta):
    def __init__(self, value: int) -> None:
        self.value = value


class Sub(Box):
    pass


class Plain:
    pass


def take(box: Box) -> None: ...


def make(kind: type[Box], n: int) -> Box:
    return kind(n)


b = Box(5)
reveal_type(b)
assert_type(b, str)
s = Sub(1)
reveal_type(s)
reveal_type(Box(2))
reveal_type(Plain())
x: Box = Box(3)
take(Box(4))
reveal_type(5)
'''


def _line(source: str, text: str) -> int:
    return next(i for i, x in enumerate(source.splitlines(), 1) if text in x)


def fire(source: str, stmt: str, kind: K, *, mypy=(), ty=(), pyright=()) -> bool:
    """Does the entry fire on ``stmt``? Each tool list holds ``(code, message, revealed_type)`` tuples."""
    ln = _line(source, stmt)

    def diags(tool, rows):
        return [Diagnostic(tool, ln, 1, Severity.ERROR, c, m, revealed_type=r) for c, m, r in rows]

    dm, dt, dp = diags(Tool.MYPY, mypy), diags(Tool.TY, ty), diags(Tool.PYRIGHT, pyright)
    d = Discrepancy("D1", kind, ln, ln, stmt, "<module>", mypy=dm, ty=dt, pyright=dp)
    st = CaseState("t", source, "3.13", {Tool.MYPY: dm, Tool.TY: dt, Tool.PYRIGHT: dp},
                   RuntimeResult(status="success"), [], {}, {}, pyright_ran=True)
    return EID in {e.id for e in matching_entries(st, d)}


def reveal(source, stmt, mypy_t, ty_t, pyright_t=None, kind=K.REVEAL_MISMATCH):
    return fire(source, stmt, kind, mypy=[(None, "", mypy_t)], ty=[("revealed-type", "", ty_t)],
                pyright=[(None, "", ty_t if pyright_t is None else pyright_t)])


# ------------------------------------------------------------------------------------------------ positives
@pytest.mark.parametrize("stmt", ["reveal_type(b)", "reveal_type(s)", "reveal_type(Box(2))"], ids=["variable", "subclass", "direct call"])
def test_reveal_of_the_class_against_the_annotated_type_is_closed(stmt):
    cls = {"reveal_type(b)": "Box", "reveal_type(s)": "Sub", "reveal_type(Box(2))": "Box"}[stmt]
    assert reveal(SRC, stmt, cls, "str")


def test_module_qualified_mypy_reveal_is_closed():
    assert reveal(SRC, "reveal_type(b)", "case.Box", "str")


def test_assert_type_against_the_annotated_type_is_closed():
    assert fire(SRC, "assert_type(b, str)", K.ONLY_MYPY,
                mypy=[("assert-type", 'Expression is of type "Box", not "str"', None)])


@pytest.mark.parametrize("stmt,code,msg", [
    ("return kind(n)", "invalid-return-type", "Return type does not match returned value: expected `Box`, found `str`"),
    ("x: Box = Box(3)", "invalid-assignment", "Object of type `str` is not assignable to `Box`"),
    ("take(Box(4))", "invalid-argument-type", "Argument to function `take` is incorrect: Expected `Box`, found `str`"),
], ids=["return through type[Box]", "assignment", "argument"])
def test_ty_rejection_of_the_annotated_type_is_closed(stmt, code, msg):
    assert fire(SRC, stmt, K.ONLY_TY, ty=[(code, msg, None)])


def test_metaclass_inherited_from_a_program_base_is_covered():
    # Sub has no metaclass keyword of its own: it inherits Box's
    assert reveal(SRC, "reveal_type(s)", "Sub", "str")


# ------------------------------------------------------------------------------------------------ controls (stay live)
@pytest.mark.parametrize("ann", ["Any", "Self", "T", "Box", "'Box'", "Box | None", "list[Box]"])
def test_metaclass_call_that_may_return_the_instance_is_not_covered(ann):
    src = SRC.replace("def __call__(cls, value: int) -> str:", f"def __call__(cls, value: int) -> {ann}:")
    assert not reveal(src, "reveal_type(b)", "Box", "str")


def test_metaclass_call_without_annotation_is_not_covered():
    src = SRC.replace("def __call__(cls, value: int) -> str:", "def __call__(cls, value: int):")
    assert not reveal(src, "reveal_type(b)", "Box", "str")


def test_pep695_type_variable_return_is_not_covered():
    src = SRC.replace("def __call__(cls, value: int) -> str:", "def __call__[U](cls, value: U) -> U:")
    assert not reveal(src, "reveal_type(b)", "Box", "str")


def test_class_without_that_metaclass_is_not_covered():
    assert not reveal(SRC, "reveal_type(Plain())", "Plain", "str")


def test_statement_that_names_no_such_class_is_not_covered():
    assert not reveal(SRC, "reveal_type(5)", "int", "str")


def test_program_without_a_metaclass_is_not_covered():
    src = "from typing import reveal_type\n\n\nclass A:\n    pass\n\n\na = A()\nreveal_type(a)\n"
    assert not reveal(src, "reveal_type(a)", "A", "str")


def test_ty_and_pyright_that_disagree_keep_the_reveal_live():
    assert not reveal(SRC, "reveal_type(b)", "Box", "str", pyright_t="int")


def test_mypy_reveal_that_is_not_the_class_stays_live():
    assert not reveal(SRC, "reveal_type(b)", "int", "str")
    assert not reveal(SRC, "reveal_type(b)", "Box | None", "str")


def test_equal_reveals_are_no_mismatch_of_this_kind():
    assert not reveal(SRC, "reveal_type(b)", "Box", "Box")


def test_reveal_without_pyright_text_stays_live():
    assert not fire(SRC, "reveal_type(b)", K.REVEAL_MISMATCH, mypy=[(None, "", "Box")], ty=[("revealed-type", "", "str")])


@pytest.mark.parametrize("msg", [
    'Expression is of type "Box", not "bytes"',      # not the annotated type
    'Expression is of type "Plain", not "str"',      # not the metaclass class
    'Expression is of type "Box", not "str" (extra)',
    "Argument 1 has incompatible type",
])
def test_other_assert_type_messages_stay_live(msg):
    assert not fire(SRC, "assert_type(b, str)", K.ONLY_MYPY, mypy=[("assert-type", msg, None)])


def test_other_mypy_code_next_to_the_assert_type_keeps_it_live():
    assert not fire(SRC, "assert_type(b, str)", K.ONLY_MYPY,
                    mypy=[("assert-type", 'Expression is of type "Box", not "str"', None), ("misc", "something else", None)])
    assert not fire(SRC, "assert_type(b, str)", K.ONLY_MYPY, mypy=[("arg-type", 'Expression is of type "Box", not "str"', None)])


@pytest.mark.parametrize("code,msg", [
    ("invalid-return-type", "Return type does not match returned value: expected `Plain`, found `str`"),   # other class
    ("invalid-return-type", "Return type does not match returned value: expected `Box`, found `bytes`"),   # other type
    ("unresolved-attribute", "Object of type `str` has no attribute `value`"),                              # other rule
    ("invalid-return-type", "Return type does not match returned value"),                                    # names nothing
])
def test_other_ty_rejections_stay_live(code, msg):
    assert not fire(SRC, "return kind(n)", K.ONLY_TY, ty=[(code, msg, None)])


def test_a_second_unrelated_ty_diagnostic_keeps_the_rejection_live():
    assert not fire(SRC, "return kind(n)", K.ONLY_TY,
                    ty=[("invalid-return-type", "Return type does not match returned value: expected `Box`, found `str`", None),
                        ("unresolved-attribute", "Object of type `Box` has no attribute `nope`", None)])


@pytest.mark.parametrize("kind", [K.CONCERN_MISMATCH, K.ONLY_PYRIGHT, K.REVEAL_UNPAIRED, K.RUNTIME_MISS])
def test_other_discrepancy_kinds_are_not_closed(kind):
    assert not fire(SRC, "reveal_type(b)", kind, mypy=[(None, "", "Box")], ty=[("revealed-type", "", "str")],
                    pyright=[(None, "", "str")])


def test_entry_is_a_non_runtime_overriding_auto_dismissal_without_selftest_example():
    e = BY_ID[EID]
    assert e.auto and e.verify is None and e.runtime_override is False
    assert set(e.kinds) == {K.REVEAL_MISMATCH, K.ONLY_MYPY, K.ONLY_TY}
    assert e.dismissal.value == "KNOWN_LIMITATION" and e.example == ""  # kb-selftest count stays at 20
    assert e.source == "https://github.com/python/mypy/issues/8595"


# ------------------------------------------------------------------------------------------------ real tools
# the shape of the two Round-10 programs (gen1_37b4e5f8 and the call_metaclass mutant): a reveal, an assert_type, a call
# through type[Box] whose result is returned as Box
REAL = '''\
from typing import assert_type, reveal_type


class Meta(type):
    def __call__(cls, value: int) -> str:
        return "wrapped:" + str(value * 2)


class Box(metaclass=Meta):
    def __new__(cls, value: int) -> "Box":
        return super().__new__(cls)

    def __init__(self, value: int) -> None:
        self.value = value


def make(kind: type[Box], n: int) -> Box:
    return kind(n)


b = Box(5)
reveal_type(b)
assert_type(b, str)
print(b, make(Box, 5))
'''

# the metaclass __call__ is annotated Any: ty and pyright treat the call as the instance, so there is nothing to close
REAL_ANY = REAL.replace("def __call__(cls, value: int) -> str:", "def __call__(cls, value: int) -> Any:").replace(
    "from typing import assert_type", "from typing import Any, assert_type")


def _pipeline():
    from typediff.llm import CachedLLM, NullLLM
    from typediff.pipeline import Pipeline, PipelineConfig

    return Pipeline(PipelineConfig(reduce=False, audit_rate=0.0), llm=CachedLLM(NullLLM()))


@needs_tools
def test_real_tools_metaclass_call_findings_are_dismissed_by_the_entry():
    from typediff.models import Tier

    rep = _pipeline().run_source(REAL, "round10-metaclass-call")
    closed = [f for f in rep.findings if f.decided_by == f"kb:{EID}"]
    assert closed and all(f.tier == Tier.DISMISSED and f.dismissal.value == "KNOWN_LIMITATION" for f in closed)
    assert not [f for f in rep.findings if f.tier != Tier.DISMISSED], [(f.discrepancy_id, f.decided_by, f.tier) for f in rep.findings]


@needs_tools
def test_real_tools_any_annotated_metaclass_call_is_not_closed_by_the_entry():
    rep = _pipeline().run_source(REAL_ANY, "round10-metaclass-call-any")
    assert not [f for f in rep.findings if f.decided_by == f"kb:{EID}"]
