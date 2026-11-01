"""kb-loop round 1: MYPY-SUITE-ALLOW-EMPTY-BODIES (matcher, positive and negative; the toggle is exercised by kb-selftest)."""

from __future__ import annotations

from typediff.kb import BY_ID, matching_entries
from typediff.models import Diagnostic, Discrepancy, DiscrepancyKind as K, RuntimeResult, Severity, Tool
from typediff.state import CaseState

HEADER = "# origin: python/mypy check-classes.test [case testX]\n"
BODY = "def f(x):\n    # type: (int) -> str\n    pass\n"


def case(src, codes=("empty-body",), kind=K.ONLY_MYPY):
    m = [Diagnostic(Tool.MYPY, 2, 1, Severity.ERROR, c, "m") for c in codes]
    st = CaseState("t", src, "3.13", {Tool.MYPY: m, Tool.TY: [], Tool.PYRIGHT: []}, RuntimeResult(status="success"), [], {}, {})
    return st, Discrepancy("D1", kind, 2, 2, "s", "", mypy=m)


def hit(st, d):
    return "MYPY-SUITE-ALLOW-EMPTY-BODIES" in {e.id for e in matching_entries(st, d)}


def test_positive_mypy_suite_program():
    assert hit(*case(HEADER + BODY))


def test_negative_program_not_from_mypy_suite():
    assert not hit(*case(BODY))
    assert not hit(*case("# origin: pyright samples\n" + BODY))


def test_negative_other_mypy_codes_alongside():
    assert not hit(*case(HEADER + BODY, codes=("empty-body", "return-value")))
    assert not hit(*case(HEADER + BODY, codes=("return",)))


def test_negative_ty_also_reports():
    st, d = case(HEADER + BODY, kind=K.CONCERN_MISMATCH)
    assert not hit(st, d)


def test_entry_requires_its_own_verifying_toggle():
    e = BY_ID["MYPY-SUITE-ALLOW-EMPTY-BODIES"]
    assert e.auto and e.verify is not None and e.verify.expects(None)["flags"] == ["--allow-empty-bodies"]


# ---------------------------------------------------------------- SUITE-EXPECTS-ERROR (hint only)


def _only(kind, src, line=3):
    code = "invalid-assignment" if kind == K.ONLY_TY else "assignment"
    d1 = Diagnostic(Tool.TY if kind == K.ONLY_TY else Tool.MYPY, line, 1, Severity.ERROR, code, "m")
    st = CaseState("t", src, "3.13", {Tool.MYPY: [d1] if kind == K.ONLY_MYPY else [], Tool.TY: [d1] if kind == K.ONLY_TY else [],
                                      Tool.PYRIGHT: []}, RuntimeResult(status="success"), [], {}, {})
    return st, Discrepancy("D1", kind, line, line, "s", "", **({"ty": [d1]} if kind == K.ONLY_TY else {"mypy": [d1]}))


def _expects(st, d):
    return "SUITE-EXPECTS-ERROR" in {e.id for e in matching_entries(st, d)}


def test_suite_expects_error_positive_and_never_auto():
    h = "# origin: ruff mdtest x.md block 0\n"
    assert _expects(*_only(K.ONLY_TY, h + "x: int = 'a'  # error: [invalid-assignment]\n", 2))
    assert _expects(*_only(K.ONLY_MYPY, h + "x: int = 'a'  # E: Incompatible types\n", 2))
    assert _expects(*_only(K.ONLY_TY, h + "# This should generate an error.\nx: int = 'a'\n", 3))
    assert BY_ID["SUITE-EXPECTS-ERROR"].auto is False


def test_suite_expects_error_negative():
    h = "# origin: ruff mdtest x.md block 0\n"
    assert not _expects(*_only(K.ONLY_TY, h + "x: int = 'a'\n", 2))  # no marker
    assert not _expects(*_only(K.ONLY_TY, "x: int = 'a'  # error: [invalid-assignment]\n", 1))  # not a harvested suite program


# ---------------------------------------------------------------- PYRIGHT-REVEAL-EXPECTED-KWARG

REVEAL_MSG = '"reveal_type" expects 1 argument'


def rk(src, msg=REVEAL_MSG, code="misc", kind=K.ONLY_MYPY):
    m = [Diagnostic(Tool.MYPY, 2, 1, Severity.ERROR, code, msg)]
    st = CaseState("t", src, "3.13", {Tool.MYPY: m, Tool.TY: [], Tool.PYRIGHT: []}, RuntimeResult(status="success"), [], {}, {})
    return st, Discrepancy("D1", kind, 2, 2, "s", "", mypy=m)


def rk_hit(st, d):
    return "PYRIGHT-REVEAL-EXPECTED-KWARG" in {e.id for e in matching_entries(st, d)}


def test_reveal_kwarg_positive():
    assert rk_hit(*rk('x = 1\nreveal_type(x, expected_text="int")\n'))
    assert rk_hit(*rk('x = 1\nreveal_type(x, expected_type=int)\n'))


def test_reveal_kwarg_negatives():
    assert not rk_hit(*rk("x = 1\nreveal_type(x, 3)\n"))  # extra positional argument: mypy is right
    assert not rk_hit(*rk('x = 1\nreveal_type(x, other=1)\n'))
    assert not rk_hit(*rk('x = 1\nreveal_type(x, expected_text="int")\n', msg='"reveal_type" expects 1 argument, 2 given'))
    assert not rk_hit(*rk('def reveal_type(*a, **k): ...\nreveal_type(1, expected_text="int")\n'))  # user-defined function
    assert not rk_hit(*rk('x = 1\nreveal_type(x, expected_text="int")\n', code="call-arg"))
