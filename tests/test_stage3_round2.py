"""Stage 3 round 2 (campaign/day2-p1): review fixes for round 1.

* ASSERT-TYPE-LITERAL-RETENTION: no Literal[True]/Literal[False] (constant-fold hole) and pyright must be silent or agree.
* ANNOTATION-ONLY-READ: recorded as a tracked mypy known limitation.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from typediff.kb import BY_ID, matching_entries
from typediff.llm import CachedLLM, NullLLM
from typediff.models import Diagnostic, Discrepancy, DiscrepancyKind as K, Dismissal, RuntimeResult, Severity, Tier, Tool
from typediff.pipeline import Pipeline, PipelineConfig
from typediff.state import CaseState
from typediff.typenorm import has_bool_literal, normalize

BIN = Path(sys.executable).parent
HAVE_TOOLS = (BIN / "mypy").exists() and (BIN / "ty").exists()
needs_tools = pytest.mark.skipif(not HAVE_TOOLS, reason="mypy/ty not installed next to the interpreter")
ROOT = Path(__file__).resolve().parents[1]

ID = "ASSERT-TYPE-LITERAL-RETENTION"
TY_MSG = "Type `{}` does not match asserted type `{}`"
MYPY_MSG = 'Expression is of type "{}", not "{}"'
PYR_MSG = '"assert_type" mismatch: expected "{}" but received "{}"'
SRC = "from typing import assert_type\nvalue = ((\"a\",),)[0][0]\nassert_type(value, str)\n"


def dg(tool, line, code, msg="m", sev=Severity.ERROR):
    return Diagnostic(tool, line, 1, sev, code, msg)


def case(src, line, actual, asserted, tool=Tool.TY, pyright=None):
    """A one-sided assert_type failure of ``tool``; ``pyright`` = list of (code, message), None = pyright did not run."""
    if tool == Tool.TY:
        x, kind = dg(Tool.TY, line, "type-assertion-failure", TY_MSG.format(actual, asserted)), K.ONLY_TY
    else:
        x, kind = dg(Tool.MYPY, line, "assert-type", MYPY_MSG.format(actual, asserted)), K.ONLY_MYPY
    p = [dg(Tool.PYRIGHT, line, code, msg) for code, msg in (pyright or [])]
    st = CaseState("t", src, "3.13", {Tool.MYPY: [], Tool.TY: [], Tool.PYRIGHT: p, tool: [x]},
                   RuntimeResult(status="success"), [], {}, {})
    st.pyright_ran = pyright is not None
    d = Discrepancy("D1", kind, line, line, "s", "", mypy=[x] if tool == Tool.MYPY else [],
                    ty=[x] if tool == Tool.TY else [], pyright=p)
    return st, d


def hit(st, d):
    return ID in {e.id for e in matching_entries(st, d)}


# ---------------------------------------------------------------- constant-fold hole


def test_has_bool_literal():
    assert has_bool_literal(normalize("Literal[True]").node)
    assert has_bool_literal(normalize("tuple[Literal[False], int]").node)
    assert has_bool_literal(normalize("Literal[1, True]").node)
    assert not has_bool_literal(normalize("Literal[1]").node)
    assert not has_bool_literal(normalize("bool").node)
    assert not has_bool_literal(normalize('tuple[Literal["True"]]').node)


FOLD_SRC = ("from typing import Literal, assert_type\n\n\nclass R(tuple[Literal[1]]):\n"
            "    def __lt__(self, other: tuple[Literal[1], ...], /) -> bool:\n        return True\n\n\n"
            "r = R((1,)) < (1,)\nassert_type(r, bool)\n")


def test_bool_literal_vs_bool_is_not_literal_retention():
    # the reviewer's program: ty folds the comparison to Literal[False], CPython gives True
    assert not hit(*case(FOLD_SRC, 10, "Literal[False]", "bool"))
    assert not hit(*case(FOLD_SRC, 10, "Literal[True]", "bool"))
    # mypy side, nested and union forms
    assert not hit(*case(FOLD_SRC, 10, "bool", "Literal[True]", tool=Tool.MYPY))
    assert not hit(*case(SRC, 3, "tuple[Literal[True]]", "tuple[bool]"))
    # an ordinary string/int literal retention is still matched
    assert hit(*case(SRC, 3, 'Literal["a"]', "str"))
    assert hit(*case(SRC, 3, "slice[Literal[1234], Any, Any]", "slice[int, Any, Any]"))


# ---------------------------------------------------------------- pyright must be silent or agree


def test_pyright_silent_or_not_run_still_matches():
    assert hit(*case(SRC, 3, 'Literal["a"]', "str", pyright=[]))
    assert hit(*case(SRC, 3, 'Literal["a"]', "str", pyright=None))


def test_pyright_same_assert_failure_agrees():
    pr = [("reportAssertTypeFailure", PYR_MSG.format("str", "Literal['a']"))]
    assert hit(*case(SRC, 3, 'Literal["a"]', "str", pyright=pr))
    # mypy as the failing tool, pyright reporting the same widened answer
    src = "from typing import Literal, assert_type\nt = (1,)\nassert_type(t, tuple[Literal[1]])\n"
    pr = [("reportAssertTypeFailure", PYR_MSG.format("tuple[Literal[1]]", "tuple[int]"))]
    assert hit(*case(src, 3, "tuple[int]", "tuple[Literal[1]]", tool=Tool.MYPY, pyright=pr))


def test_pyright_other_error_or_other_answer_keeps_finding_visible():
    # reportOperatorIssue on the same statement is not swallowed
    pr = [("reportAssertTypeFailure", PYR_MSG.format("str", "Literal['a']")), ("reportOperatorIssue", "Operator not supported")]
    assert not hit(*case(SRC, 3, 'Literal["a"]', "str", pyright=pr))
    assert not hit(*case(SRC, 3, 'Literal["a"]', "str", pyright=[("reportOperatorIssue", "Operator not supported")]))
    # pyright fails the assertion with a different received type (Unknown / another literal)
    assert not hit(*case(SRC, 3, 'Literal["a"]', "str", pyright=[("reportAssertTypeFailure", PYR_MSG.format("str", "Unknown"))]))
    assert not hit(*case(SRC, 3, 'Literal["a"]', "str", pyright=[("reportAssertTypeFailure", PYR_MSG.format("str", "Literal['b']"))]))
    # pyright warning-free but other code
    assert not hit(*case(SRC, 3, 'Literal["a"]', "str", pyright=[("reportAssertTypeFailure", "unparseable message")]))


# ---------------------------------------------------------------- the reviewer's program through the real pipeline


@needs_tools
def test_constant_fold_program_stays_in_review():
    src = (ROOT / "calibration" / "must_stay_live" / "ty_constant_fold_tuple_subclass.py").read_text()
    p = Pipeline(PipelineConfig(reduce=False, audit_rate=0.0, use_pyright=False), llm=CachedLLM(NullLLM()))
    rep = p.run_source(src, "fold-hole")
    assert rep.findings, "ty's Literal[False] vs CPython's True must still be reported"
    assert not any(f.tier == Tier.DISMISSED for f in rep.findings), [(f.decided_by, f.tier) for f in rep.findings]
    assert all(f.decided_by != f"kb:{ID}" for f in rep.findings)


@needs_tools
def test_real_literal_retention_example_is_still_closed():
    p = Pipeline(PipelineConfig(reduce=False, audit_rate=0.0, use_pyright=False), llm=CachedLLM(NullLLM()))
    rep = p.run_source(BY_ID[ID].example, "retention-example")
    assert rep.findings and all(f.decided_by == f"kb:{ID}" and f.tier == Tier.DISMISSED for f in rep.findings)


def test_inference_downstream_does_not_trust_an_evaluated_bool_literal():
    # the older INFERENCE-DOWNSTREAM entry had the same hole: probe `r` = Literal[False] (ty) vs bool (mypy)
    def run(m, t):
        st, d = case(FOLD_SRC, 10, "Literal[False]", "bool")
        st.probe_cache = {d.id: {"r": {"mypy": m, "ty": t}}}
        return "INFERENCE-DOWNSTREAM" in {e.id for e in matching_entries(st, d)}

    assert not run("bool", "Literal[False]")
    assert not run("Literal[True]", "bool")
    assert run("int", "Literal[1]")  # ordinary literal retention is unchanged


# ---------------------------------------------------------------- ANNOTATION-ONLY-READ is a tracked mypy limitation


def test_annotation_only_read_is_recorded_as_tracked_mypy_limitation():
    e = BY_ID["ANNOTATION-ONLY-READ"]
    assert e.dismissal == Dismissal.KNOWN_LIMITATION
    assert e.source.endswith("python/mypy/issues/15416")
    for n in ("15416", "17373", "4019"):
        assert f"python/mypy#{n}" in e.text
    # behaviour unchanged: still auto, still not demoted by the NameError that confirms ty's own diagnostic
    assert e.auto and e.runtime_override is False
