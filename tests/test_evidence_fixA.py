"""Evidence-layer fixes: reporter-confirmed NameError and stub-bodied probe values."""

from __future__ import annotations

from typediff.discrepancy import find_discrepancies
from typediff.models import (
    Diagnostic, DiscrepancyKind as K, RuntimeProbe, RuntimeResult, Severity, Tool,
)
from typediff.rules import attach_runtime_evidence
from typediff.state import CaseState


def diag(tool, line, code, msg="m", rev=None, sev=Severity.ERROR):
    return Diagnostic(tool, line, 1, sev, code, msg, revealed_type=rev)


def state(src, diags, rt):
    return CaseState("t", src, "3.12", diags, rt, [], {}, {})


def strong_bug(d):
    return [e for e in d.evidence if e.supports == "bug" and e.strength == "strong"]


SRC = "x: int\nprint(x)\n"
NAME_RT = dict(status="exception", exc_type="NameError", exc_message="name 'x' is not defined", exc_line=2,
               frames=[(2, "<module>")], executed_lines=[1, 2])


def test_nameerror_confirming_reporter_is_not_strong():
    ty = diag(Tool.TY, 2, "unresolved-reference", "Name `x` used when not defined")
    st = state(SRC, {Tool.MYPY: [], Tool.TY: [ty]}, RuntimeResult(**NAME_RT))
    d = next(x for x in find_discrepancies(st.diags, st.amap, st.runtime) if x.kind == K.ONLY_TY)
    attach_runtime_evidence(st, d)
    assert not strong_bug(d)
    assert not any(e.blame == "mypy" for e in d.evidence)
    assert any("confirms the reporting tool" in e.summary for e in d.evidence)


def test_nameerror_nobody_reported_stays_strong():
    other = diag(Tool.TY, 2, "invalid-argument-type", "Argument is incorrect")
    st = state(SRC, {Tool.MYPY: [], Tool.TY: [other]}, RuntimeResult(**NAME_RT))
    d = next(x for x in find_discrepancies(st.diags, st.amap, st.runtime) if x.kind == K.ONLY_TY)
    attach_runtime_evidence(st, d)
    assert len(strong_bug(d)) == 1


def test_runtime_miss_nameerror_stays_strong():
    st = state(SRC, {Tool.MYPY: [], Tool.TY: []}, RuntimeResult(**NAME_RT))
    d = next(x for x in find_discrepancies(st.diags, st.amap, st.runtime) if x.kind == K.RUNTIME_MISS)
    attach_runtime_evidence(st, d)
    assert len(strong_bug(d)) == 1


JOIN = "from typing import TypeVar\nT = TypeVar('T')\ndef join(x: T, y: T) -> T: ...\nreveal_type(join(1, 'a'))\n"
JOIN_BODY = "from typing import TypeVar\nT = TypeVar('T')\ndef join(x: T, y: T) -> T:\n    pass\nreveal_type(join(1, 'a'))\n"


def _probe_state(src, shape):
    n = len(src.splitlines())
    rt = RuntimeResult(status="success", probes=[RuntimeProbe(n, shape)], executed_lines=list(range(1, n + 1)))
    return state(src, {Tool.MYPY: [diag(Tool.MYPY, n, None, rev="builtins.int", sev=Severity.NOTE)],
                       Tool.TY: [diag(Tool.TY, n, "revealed-type", rev="str", sev=Severity.NOTE)]}, rt)


NONE_SHAPE = {"type": "builtins.NoneType", "mro": ["builtins.NoneType", "builtins.object"], "repr": "None"}


def test_stub_bodied_none_probe_not_strong():
    for src in (JOIN, JOIN_BODY):
        st = _probe_state(src, NONE_SHAPE)
        d = find_discrepancies(st.diags, st.amap, st.runtime)[0]
        attach_runtime_evidence(st, d)
        assert not strong_bug(d), d.evidence
        assert any("stub-bodied" in e.summary for e in d.evidence)


def test_real_function_probe_still_strong():
    src = JOIN.replace("T: ...", "T:\n    return x")
    st = _probe_state(src, {"type": "builtins.float", "mro": ["builtins.float", "builtins.object"], "repr": "1.5"})
    d = find_discrepancies(st.diags, st.amap, st.runtime)[0]
    attach_runtime_evidence(st, d)
    assert strong_bug(d)


def test_none_probe_from_non_stub_still_strong():
    src = JOIN.replace("T: ...", "T:\n    print(x)")
    st = _probe_state(src, NONE_SHAPE)
    d = find_discrepancies(st.diags, st.amap, st.runtime)[0]
    attach_runtime_evidence(st, d)
    assert strong_bug(d)
