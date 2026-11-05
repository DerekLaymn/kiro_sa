"""Day 7: `only_pyright` discrepancy kind (pyright errors that mypy and ty both miss, with CPython evidence).

Opt-in (``PipelineConfig.pyright_only`` / ``--pyright-only``); with the switch off nothing changes."""

from __future__ import annotations

import json

from typediff.anchors import AnchorMap
from typediff.dataset import signature
from typediff.discrepancy import find_discrepancies, pyright_runtime_relation
from typediff.llm import CachedLLM, NullLLM
from typediff.models import (
    Diagnostic, Discrepancy, DiscrepancyKind as K, Finding, RuntimeResult, Severity, Symptom, Tier, Tool, Verdict,
    to_jsonable,
)
from typediff.pipeline import Pipeline, PipelineConfig
from typediff.replay import readjudicate
from typediff.report import render_summary
from typediff.state import CaseState

SRC = "x: int = 'a'\nprint(x)\n"
CALL = "def f(x: int) -> int:\n    return x + 1\n\n\nf('a')\n"  # f('a') is line 5, the TypeError is raised on line 2


def pyr(line, code="reportAssignmentType", msg='Type "str" is not assignable to declared type "int"', sev=Severity.ERROR):
    return Diagnostic(Tool.PYRIGHT, line, 1, sev, code, msg)


def other(tool, line, code="assignment", msg="Incompatible types"):
    return Diagnostic(tool, line, 1, Severity.ERROR, code, msg)


def ran(lines):
    return RuntimeResult(status="success", executed_lines=list(lines))


def kinds(src, diags, runtime, flag=True):
    return [d for d in find_discrepancies(diags, AnchorMap(src), runtime, pyright_only=flag)]


def only(ds):
    return [d for d in ds if d.kind == K.ONLY_PYRIGHT]


# ---------------------------------------------------------------- discrepancy extraction


def test_off_by_default_no_discrepancy():
    diags = {Tool.MYPY: [], Tool.TY: [], Tool.PYRIGHT: [pyr(1)]}
    assert find_discrepancies(diags, AnchorMap(SRC), ran([1, 2])) == []
    assert kinds(SRC, diags, ran([1, 2]), flag=False) == []


def test_executed_statement_is_runtime_contradicts():
    diags = {Tool.MYPY: [], Tool.TY: [], Tool.PYRIGHT: [pyr(1)]}
    (d,) = only(kinds(SRC, diags, ran([1, 2])))
    assert (d.anchor, d.mypy, d.ty) == (1, [], [])
    assert [x.code for x in d.pyright] == ["reportAssignmentType"]
    assert d.reveal_relation == "runtime_contradicts" and d.priority == 0.3


def test_statement_that_never_ran_has_no_runtime_evidence():
    diags = {Tool.MYPY: [], Tool.TY: [], Tool.PYRIGHT: [pyr(1)]}
    assert only(kinds(SRC, diags, ran([2]))) == []


def test_unknown_coverage_has_no_runtime_evidence():
    diags = {Tool.MYPY: [], Tool.TY: [], Tool.PYRIGHT: [pyr(1)]}
    assert only(kinds(SRC, diags, RuntimeResult(status="success"))) == []
    assert only(kinds(SRC, diags, RuntimeResult(status="harness_error"))) == []


def test_mypy_or_ty_reporting_at_the_statement_means_not_pyright_only():
    for tool in (Tool.MYPY, Tool.TY):
        diags = {Tool.MYPY: [], Tool.TY: [], Tool.PYRIGHT: [pyr(1)]}
        diags[tool] = [other(tool, 1)]
        assert only(kinds(SRC, diags, ran([1, 2]))) == []


def test_other_statement_flagged_by_mypy_does_not_hide_it():
    src = "x: int = 'a'\ny: int = 'b'\n"
    diags = {Tool.MYPY: [other(Tool.MYPY, 2)], Tool.TY: [], Tool.PYRIGHT: [pyr(1)]}
    ds = only(kinds(src, diags, ran([1, 2])))
    assert [d.anchor for d in ds] == [1]


def test_pyright_warnings_and_reveals_are_not_findings():
    diags = {Tool.MYPY: [], Tool.TY: [], Tool.PYRIGHT: [
        pyr(1, "reportSelfClsParameterName", "style", Severity.WARNING),
        Diagnostic(Tool.PYRIGHT, 1, 1, Severity.NOTE, None, 'Type of "x" is "int"', revealed_type="int")]}
    assert only(kinds(SRC, diags, ran([1, 2]))) == []


def test_type_exception_below_the_pyright_statement_is_runtime_supports():
    rt = RuntimeResult(status="exception", exc_type="TypeError",
                       exc_message='can only concatenate str (not "int") to str', exc_line=2,
                       frames=[(5, "<module>"), (2, "f")], executed_lines=[1, 2, 5])
    diags = {Tool.MYPY: [], Tool.TY: [], Tool.PYRIGHT: [pyr(5, "reportArgumentType", "Argument of type str")]}
    ds = kinds(CALL, diags, rt)
    (d,) = only(ds)
    assert d.anchor == 5 and d.reveal_relation == "runtime_supports" and d.priority == 0.7
    assert K.RUNTIME_MISS in {x.kind for x in ds}  # the inner frame stays a runtime_miss; ids of old kinds do not move
    assert [x.id for x in ds].index(d.id) == len(ds) - 1  # appended last


def test_no_duplicate_next_to_runtime_miss_at_the_same_statement():
    rt = RuntimeResult(status="exception", exc_type="TypeError", exc_message="unsupported operand type(s) for +",
                       exc_line=2, frames=[(2, "f")], executed_lines=[1, 2])
    diags = {Tool.MYPY: [], Tool.TY: [], Tool.PYRIGHT: [pyr(2, "reportOperatorIssue", "Operator + not supported")]}
    ds = kinds("def f():\n    return 'a' + 1\n", diags, rt)
    assert [d.kind for d in ds] == [K.RUNTIME_MISS]
    assert [x.code for x in ds[0].pyright] == ["reportOperatorIssue"]


def test_non_type_exception_is_no_evidence():
    rt = RuntimeResult(status="exception", exc_type="ZeroDivisionError", exc_message="division by zero", exc_line=1,
                       frames=[(1, "<module>")], executed_lines=[1])
    am = AnchorMap("x = 1 / 0\n")
    assert pyright_runtime_relation(am, rt, 1) is None


def test_relation_helper():
    am = AnchorMap(SRC)
    assert pyright_runtime_relation(am, ran([1]), 1) == "contradicts"
    assert pyright_runtime_relation(am, ran([2]), 1) is None
    assert pyright_runtime_relation(am, RuntimeResult(status="timeout"), 1) is None


def test_multiline_statement_counts_as_executed_on_any_of_its_lines():
    src = "x = foo(\n    1,\n    2,\n)\n"
    am = AnchorMap(src)
    assert pyright_runtime_relation(am, ran([3]), 1) == "contradicts"
    assert pyright_runtime_relation(am, ran([5]), 1) is None


# ---------------------------------------------------------------- pipeline: findings, evidence, replay


def state(src, diags, runtime):
    return CaseState("t", src, "3.13", diags, runtime, [], {}, {}, pyright_ran=True)


def pipe(flag):
    return Pipeline(PipelineConfig(reduce=False, audit_rate=0.0, pyright_only=flag), llm=CachedLLM(NullLLM()))


def test_pipeline_surfaces_a_review_finding_with_evidence():
    st = state(SRC, {Tool.MYPY: [], Tool.TY: [], Tool.PYRIGHT: [pyr(1)]}, ran([1, 2]))
    rep = pipe(True)._judge(st)
    (d,) = only(rep.discrepancies)
    (f,) = [x for x in rep.findings if x.discrepancy_id == d.id]
    assert f.tier == Tier.REVIEW and f.dismissal is None
    assert any("only pyright reports" in e.summary and "does not back pyright" in e.summary for e in f.evidence)
    text = render_summary(rep)
    assert "kind: only_pyright" in text and "pyright: L1:1 error[reportAssignmentType]" in text


def test_pipeline_supports_case_carries_strong_runtime_evidence():
    rt = RuntimeResult(status="exception", exc_type="TypeError",
                       exc_message='can only concatenate str (not "int") to str', exc_line=2,
                       frames=[(5, "<module>"), (2, "f")], executed_lines=[1, 2, 5])
    st = state(CALL, {Tool.MYPY: [], Tool.TY: [], Tool.PYRIGHT: [pyr(5, "reportArgumentType", "Argument of type str")]}, rt)
    rep = pipe(True)._judge(st)
    d = next(x for x in rep.discrepancies if x.kind == K.ONLY_PYRIGHT)
    f = next(x for x in rep.findings if x.discrepancy_id == d.id)
    assert f.tier == Tier.REVIEW
    assert any(e.type.value == "RUNTIME" and e.supports == "bug" and e.blame == "both" for e in f.evidence)
    assert any("matches the runtime" in e.summary for e in f.evidence)


def test_pipeline_default_config_adds_nothing():
    st = state(SRC, {Tool.MYPY: [], Tool.TY: [], Tool.PYRIGHT: [pyr(1)]}, ran([1, 2]))
    rep = pipe(False)._judge(st)
    assert rep.discrepancies == [] and rep.findings == []


def test_flag_is_ignored_when_pyright_did_not_run():
    st = CaseState("t", SRC, "3.13", {Tool.MYPY: [], Tool.TY: []}, ran([1, 2]), [], {}, {})
    assert pipe(True)._judge(st).discrepancies == []


def test_replay_of_a_saved_report_with_the_switch_on_adds_only_the_new_kind():
    src = "x: int = 'a'\ny: int = 'b'\n"
    diags = {Tool.MYPY: [other(Tool.MYPY, 2)], Tool.TY: [other(Tool.TY, 2)], Tool.PYRIGHT: [pyr(1), pyr(2)]}
    old = pipe(False)._judge(state(src, diags, ran([1, 2])))
    saved = json.loads(json.dumps(to_jsonable(old)))
    new = readjudicate(pipe(True), saved)
    assert all(d.kind != K.ONLY_PYRIGHT for d in old.discrepancies)
    added = only(new.discrepancies)
    assert [d.anchor for d in added] == [1]
    assert [(d.id, d.kind) for d in new.discrepancies if d.kind != K.ONLY_PYRIGHT] == [(d.id, d.kind) for d in old.discrepancies]


def test_signature_separates_pyright_only_findings_by_rule():
    a = Discrepancy("D1", K.ONLY_PYRIGHT, 1, 1, "s", "", pyright=[pyr(1, "reportCallIssue", "Expected 1 positional")])
    b = Discrepancy("D1", K.ONLY_PYRIGHT, 1, 1, "s", "", pyright=[pyr(1, "reportAttributeAccessIssue", 'Cannot access "x"')])

    def f(d):
        return Finding(d.id, Verdict.BUG, Tier.CANDIDATE, "unknown", Symptom.FALSE_NEGATIVE, None, 0.5, "gate")

    assert signature(f(a), a) != signature(f(b), b)
    assert signature(f(a), a) == signature(f(a), a)
