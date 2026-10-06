"""Regression tests for the high-impact bugs found in the typediff stage audit. No LLM is ever called."""

from __future__ import annotations

import stat
import sys
from pathlib import Path

import pytest

from typediff.adjudicator import Adjudicator
from typediff.corpus import Corpus
from typediff.discrepancy import find_discrepancies
from typediff.experiments import ExperimentResult, ExperimentRunner
from typediff.kb import BY_ID, matched_probe, runtime_contradiction
from typediff.llm import CachedLLM, NullLLM
from typediff.models import (
    Diagnostic, Discrepancy, DiscrepancyKind as K, Dismissal, Evidence, EvidenceType, Finding, RuntimeProbe,
    RuntimeResult, Severity, Tier, Tool, Verdict,
)
from typediff.parsers import parse_mypy, parse_runtime, parse_ty
from typediff.pipeline import Pipeline, PipelineConfig
from typediff.rules import attach_runtime_evidence, crash_findings, deterministic_stage
from typediff.runners import Runners, ToolConfig
from typediff.state import CaseState

BIN = Path(sys.executable).parent
HAVE_TOOLS = (BIN / "mypy").exists() and (BIN / "ty").exists()
needs_tools = pytest.mark.skipif(not HAVE_TOOLS, reason="mypy/ty not installed next to the interpreter")

EQ_EXAMPLE = BY_ID["TY-STRICT-EQUALITY"].example


def diag(tool, line, code, msg="m", sev=Severity.ERROR, rev=None, col=1):
    return Diagnostic(tool, line, col, sev, code, msg, revealed_type=rev)


def offline_state(source="x = 1\n", diags=None, runtime=None):
    return CaseState("t", source, "3.12", diags or {Tool.MYPY: [], Tool.TY: []},
                     runtime or RuntimeResult(status="success"), [], {}, {})


def wrapper(tmp_path: Path, body: str) -> list[str]:
    """A ty stand-in: `body` runs first (sh), otherwise the real ty is executed."""
    p = tmp_path / "ty_stub.sh"
    p.write_text(f"#!/bin/sh\n{body}\nexec {BIN / 'ty'} \"$@\"\n")
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return [str(p)]


def real_state(src, runners):
    diags, crashes = {}, []
    for t in (Tool.MYPY, Tool.TY):
        r = runners.check(t, src)
        diags[t], crashes = r.diagnostics, crashes + r.crashes
    st = CaseState("t", src, "3.12", diags, runners.run_runtime(src), crashes, {}, {}, runners=runners)
    return st, find_discrepancies(st.diags, st.amap, st.runtime, st.module)


# --------------------------------------------------------------------------- 1. config_toggle


@needs_tools
def test_config_toggle_failed_run_is_inconclusive(tmp_path):
    body = 'case "$*" in *strict-equality-semantics*) echo "error: unknown option" >&2; exit 2;; esac'
    good, bad = Runners(ToolConfig()), Runners(ToolConfig(ty_cmd=wrapper(tmp_path, body)))
    req = {"tool": "ty", "flags": ["--config", "analysis.strict-equality-semantics=true"]}
    st, ds = real_state(EQ_EXAMPLE, good)
    d = next(x for x in ds if x.kind == K.ONLY_MYPY)
    ok = ExperimentRunner(st).config_toggle(d, req)
    assert ok.ok and ok.evidence.supports == "not_bug"  # control: a healthy toggle still dismisses
    st.runners = bad
    res = ExperimentRunner(st).config_toggle(d, req)
    assert not res.ok and res.evidence is None and "inconclusive" in res.summary


@needs_tools
def test_failing_toggle_never_dismisses_via_kb(tmp_path):
    body = 'case "$*" in *strict-equality-semantics*) exit 2;; esac'
    runners = Runners(ToolConfig(ty_cmd=wrapper(tmp_path, body)))
    p = Pipeline(PipelineConfig(reduce=False, audit_rate=0.0, use_pyright=False), llm=CachedLLM(NullLLM()), runners=runners)
    rep = p.run_source(EQ_EXAMPLE, "toggle-fail")
    assert rep.findings and not any(f.tier == Tier.DISMISSED for f in rep.findings)


# --------------------------------------------------------------------------- 2. probe matching

TWO_REVEALS = "a = 1; b = 'x'\nprint(reveal_type(a), reveal_type(b))\n"


@needs_tools
def test_probes_matched_by_order_not_mixed():
    st, ds = real_state(TWO_REVEALS, Runners(ToolConfig()))
    assert len(st.runtime.probes) == 2
    revs = [d for d in ds if d.kind in (K.REVEAL_MISMATCH, K.REVEAL_UNPAIRED)]
    for d in revs:
        attach_runtime_evidence(st, d)
        assert not any(e.supports == "bug" for e in d.evidence), d.evidence
        assert runtime_contradiction(st, d) is None
    # positive control: the k-th reveal gets the k-th probe
    reveals = sorted((x for x in st.diags[Tool.TY] if x.revealed_type is not None), key=lambda x: x.col or 0)
    assert len(reveals) == 2
    for x, repr_ in zip(reveals, ("1", "'x'")):
        d = Discrepancy("Dx", K.REVEAL_MISMATCH, 2, 2, "print(...)", "", ty=[x])
        assert matched_probe(st, d, "ty").shape["repr"] == repr_


def test_ambiguous_probes_are_neutral_and_do_not_block():
    src = "for i in range(3):\n    reveal_type(i)\n"
    probes = [RuntimeProbe(2, {"type": "int", "mro": ["int", "object"], "repr": str(i)}) for i in range(3)]
    rt = RuntimeResult(status="success", probes=probes, executed_lines=[1, 2])
    st = offline_state(src, {Tool.MYPY: [diag(Tool.MYPY, 2, None, rev="builtins.str", sev=Severity.NOTE)],
                             Tool.TY: [diag(Tool.TY, 2, "revealed-type", rev="int", sev=Severity.NOTE)]}, rt)
    d = find_discrepancies(st.diags, st.amap, st.runtime)[0]
    assert d.kind == K.REVEAL_MISMATCH
    assert matched_probe(st, d, "mypy") is None and runtime_contradiction(st, d) is None
    attach_runtime_evidence(st, d)
    assert not any(e.supports == "bug" for e in d.evidence)
    assert any("cannot be paired" in e.summary for e in d.evidence)


def test_matching_probe_still_gives_bug_evidence():
    src = "x = 1\nreveal_type(x)\n"
    rt = RuntimeResult(status="success", probes=[RuntimeProbe(2, {"type": "int", "mro": ["int", "object"], "repr": "1"})],
                       executed_lines=[1, 2])
    st = offline_state(src, {Tool.MYPY: [diag(Tool.MYPY, 2, None, rev="builtins.str", sev=Severity.NOTE)],
                             Tool.TY: [diag(Tool.TY, 2, "revealed-type", rev="int", sev=Severity.NOTE)]}, rt)
    d = find_discrepancies(st.diags, st.amap, st.runtime)[0]
    attach_runtime_evidence(st, d)
    assert [e.blame for e in d.evidence if e.supports == "bug"] == ["mypy"]
    assert "outside mypy" in runtime_contradiction(st, d)


# --------------------------------------------------------------------------- 3. parsers


def test_user_text_internal_error_is_not_a_crash():
    out = 'case.py:3:13: note: Revealed type is "Literal[\'INTERNAL ERROR\']"\n'
    _, crashes = parse_mypy(out, "", 1, "case.py")
    assert crashes == []


def test_real_mypy_internal_error_still_detected():
    out = "case.py: error: INTERNAL ERROR -- Please try using mypy master on GitHub:\n"
    _, crashes = parse_mypy(out, "", 2, "case.py")
    assert len(crashes) == 1 and crashes[0].kind == "internal_error"


def test_timeout_word_in_plain_runtime_text():
    assert parse_runtime("ok: done, no timeout here").status == "success"
    assert parse_runtime("TIMEOUT after 15s").status == "timeout"


# --------------------------------------------------------------------------- 4. abnormal exit codes


def test_abnormal_exit_without_diagnostics_is_not_no_errors():
    _, mc = parse_mypy("", "usage: mypy ...\nmypy: error: bad flag", 2, "case.py")
    _, tc = parse_ty("", "error: unexpected argument", 2, "case.py")
    assert [c.kind for c in mc] == ["abnormal_exit"] and [c.kind for c in tc] == ["abnormal_exit"]
    fs = crash_findings(mc + tc)
    assert all(f.tier == Tier.REVIEW and f.verdict == Verdict.NEEDS_HUMAN for f in fs)


def test_normal_exit_codes_and_mypy_syntax_error_are_not_crashes():
    assert parse_mypy("", "", 0, "case.py")[1] == [] and parse_mypy("", "", 1, "case.py")[1] == []
    assert parse_ty("", "", 0, "case.py")[1] == [] and parse_ty("", "", 1, "case.py")[1] == []
    d, c = parse_mypy("case.py:1: error: invalid syntax  [syntax]\n", "", 2, "case.py")
    assert d and c == []  # mypy exits 2 for blocking errors but did print diagnostics
    assert parse_ty("", "", 101, "case.py")[1][0].kind == "panic"


@needs_tools
def test_broken_ty_run_creates_no_spurious_only_mypy(tmp_path):
    runners = Runners(ToolConfig(ty_cmd=[*wrapper(tmp_path, 'case "$1" in check) echo "error: boom" >&2; exit 2;; esac')]))
    p = Pipeline(PipelineConfig(reduce=False, audit_rate=0.0, use_pyright=False), llm=CachedLLM(NullLLM()), runners=runners)
    rep = p.run_source("x: int = 'a'\n", "broken-ty")
    assert not rep.discrepancies
    assert any(c.kind == "abnormal_exit" for c in rep.crashes)
    assert all(f.tier == Tier.REVIEW for f in rep.findings)


# --------------------------------------------------------------------------- 5. gate fail-closed


def _adj():
    return Adjudicator(CachedLLM(NullLLM()), Corpus())


def _ev(etype, supports):
    return Evidence(etype, supports, "s", verified=True, strength="strong")


def _bug(notes):
    return Finding("D1", Verdict.BUG, Tier.REVIEW, "ty", None, None, 0.95, "llm",
                   evidence=[_ev(EvidenceType.RUNTIME, "bug")], review_notes=list(notes))


def _notbug(conf, notes):
    return Finding("D1", Verdict.NOT_BUG, Tier.REVIEW, "none", None, Dismissal.NOISE, conf, "llm",
                   evidence=[_ev(EvidenceType.KB, "not_bug")], review_notes=list(notes))


def test_gate_bug_needs_a_skeptic_pass():
    a = _adj()
    assert a.gate(_bug(["SKEPTIC:UNAVAILABLE"])).tier == Tier.CANDIDATE
    assert a.gate(_bug([])).tier == Tier.CANDIDATE
    assert a.gate(_bug(["SKEPTIC:AGREE: fine"])).tier == Tier.CONFIRMED  # control: healthy skeptic still confirms


def test_gate_dismissal_needs_advocate_when_required():
    a = _adj()
    assert a.gate(_notbug(0.9, ["ADVOCATE:UNAVAILABLE"])).tier == Tier.REVIEW
    assert a.gate(_notbug(0.9, [])).tier == Tier.REVIEW
    assert a.gate(_notbug(0.99, ["AUDIT: x", "ADVOCATE:UNAVAILABLE"])).tier == Tier.REVIEW
    assert a.gate(_notbug(0.9, ["ADVOCATE:UPHOLD_DISMISSAL: ok"])).tier == Tier.DISMISSED
    assert a.gate(_notbug(0.99, [])).tier == Tier.DISMISSED  # advocate not required at >= 0.95 unaudited


# --------------------------------------------------------------------------- 6. _verify_evidence


def _disc(kb=(), evidence=()):
    return Discrepancy("D1", K.ONLY_TY, 1, 1, "x = 1", "", ty=[diag(Tool.TY, 1, "unresolved-attribute")],
                       kb_hits=list(kb), evidence=list(evidence))


def _verify(d, raw, results=()):
    st = offline_state()
    ex = ExperimentRunner(st)
    ex.results.extend(results)
    return _adj()._verify_evidence(st, d, raw, ex)


def test_kb_hint_only_entry_never_verifies():
    assert not BY_ID["TY-ONLY-CHECK"].auto
    (ev,) = _verify(_disc(kb=["TY-ONLY-CHECK"]), [{"type": "KB", "supports": "not_bug", "citation": "KB:TY-ONLY-CHECK"}])
    assert not ev.verified


def test_kb_auto_entry_verifies_but_verify_required_entry_needs_its_experiment():
    (ev,) = _verify(_disc(kb=["TY-CALLABLE-DUNDER"]), [{"type": "KB", "supports": "not_bug", "citation": "KB:TY-CALLABLE-DUNDER"}])
    assert ev.verified
    raw = [{"type": "KB", "supports": "not_bug", "citation": "KB:TY-STRICT-EQUALITY"}]
    assert not _verify(_disc(kb=["TY-STRICT-EQUALITY"]), raw)[0].verified
    done = Evidence(EvidenceType.EXPERIMENT, "not_bug", "toggle", citation="E1", verified=True)
    assert _verify(_disc(kb=["TY-STRICT-EQUALITY"], evidence=[done]), raw)[0].verified
    assert not _verify(_disc(kb=[]), raw)[0].verified  # id did not match this discrepancy


def test_experiment_evidence_must_support_claimed_direction():
    neutral = Evidence(EvidenceType.EXPERIMENT, "neutral", "persists", verified=True)
    toggled = Evidence(EvidenceType.EXPERIMENT, "not_bug", "gone", verified=True)
    results = [ExperimentResult("E1", "config_toggle", {}, True, "persists", {}, neutral, "D1"),
               ExperimentResult("E2", "config_toggle", {}, True, "gone", {}, toggled, "D1"),
               ExperimentResult("E3", "config_toggle", {}, False, "rejected", {}, None, "D1"),
               ExperimentResult("E4", "config_toggle", {}, True, "gone", {}, toggled, "D2")]

    def check(cit, supports="not_bug"):
        return _verify(_disc(), [{"type": "EXPERIMENT", "supports": supports, "citation": cit}], results)[0].verified

    assert not check("E1")  # experiment recorded "persists"
    assert check("E2")
    assert not check("E2", "bug")  # right id, wrong direction
    assert not check("E3") and not check("E4") and not check("E99")
    assert check("E1", "neutral")


# --------------------------------------------------------------------------- 7. severity-only / @Todo


def test_severity_only_dismissal_carries_evidence():
    m = diag(Tool.MYPY, 1, "attr-defined", sev=Severity.WARNING)
    t = diag(Tool.TY, 1, "unresolved-attribute")
    from typediff.concerns import same_concern

    assert same_concern(m, t)
    d = Discrepancy("D1", K.SEVERITY_ONLY, 1, 1, "x.y", "", mypy=[m], ty=[t])
    decided, remaining = deterministic_stage(offline_state("x.y\n", {Tool.MYPY: [m], Tool.TY: [t]}), [d],
                                             ExperimentRunner(offline_state()))
    f = decided["D1"]
    assert f.decided_by == "rule:severity-only" and not remaining
    (ev,) = f.evidence
    assert ev.verified and ev.supports == "not_bug" and "warning[attr-defined]" in ev.summary and "error[unresolved-attribute]" in ev.summary


def _todo_case(exception):
    src = "x = 1 + 'a'\n"
    t = diag(Tool.TY, 1, "unresolved-attribute", msg="Type `@Todo` has no attribute")
    rt = (RuntimeResult(status="exception", exc_type="TypeError", exc_message="unsupported operand", exc_line=1,
                        frames=[(1, "<module>")], executed_lines=[1])
          if exception else RuntimeResult(status="success", executed_lines=[1]))
    st = offline_state(src, {Tool.MYPY: [], Tool.TY: [t]}, rt)
    d = Discrepancy("D1", K.ONLY_TY, 1, 1, "x = 1 + 'a'", "", ty=[t])
    return st, d


def test_todo_dismissal_respects_runtime_contradiction():
    st, d = _todo_case(exception=False)
    decided, remaining = deterministic_stage(st, [d], ExperimentRunner(st))
    assert decided["D1"].decided_by == "kb:TY-TODO"  # control
    st, d = _todo_case(exception=True)
    decided, remaining = deterministic_stage(st, [d], ExperimentRunner(st))
    assert "D1" not in decided and remaining == [d]
    assert "TY-TODO" in d.kb_hits
