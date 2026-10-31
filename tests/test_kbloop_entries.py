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
