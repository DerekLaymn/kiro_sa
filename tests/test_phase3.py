"""Regression tests for the ty#4656 lessons (Phase 3). No LLM is ever called.

ty#4656 turned out to be INTENDED behaviour, so these tests check that the pipeline is robust around that case
without turning "Self parameter" into a general rule: every rule is narrow and defaults to human review.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from typediff import priors as priors_mod
from typediff.adjudicator import Adjudicator, kb_entry_eligible
from typediff.corpus import Corpus
from typediff.discrepancy import find_discrepancies
from typediff.experiments import (
    ExperimentResult, ExperimentRunner, call_assignability_oracle, reveal_is_display_sensitive,
)
from typediff.kb import BY_ID, entry_demotion, m_precision_runtime_consistent, matching_entries
from typediff.llm import CachedLLM, NullLLM
from typediff.models import (
    CaseReport, Crash, Diagnostic, Discrepancy, DiscrepancyKind as K, Evidence, EvidenceType, Finding, RuntimeProbe,
    RuntimeResult, Severity, Tier, Tool, ToolRun, Verdict,
)
from typediff.pipeline import Pipeline, PipelineConfig
from typediff.priors import apply_prior_cap, find_priors
from typediff.reducer import Reducer
from typediff.report import draft_issue
from typediff.rules import attach_runtime_evidence, crash_findings, deterministic_stage
from typediff.runners import CheckResult, Runners, ToolConfig
from typediff.state import CaseState

BIN = Path(sys.executable).parent
HAVE_TOOLS = (BIN / "mypy").exists() and (BIN / "ty").exists()
needs_tools = pytest.mark.skipif(not HAVE_TOOLS, reason="mypy/ty not installed next to the interpreter")
EXAMPLES = Path(__file__).resolve().parents[1] / "examples"

SELF_SRC = """from typing import Self


class Node:
    def add(self, c: Self) -> Self:
        return self


class Leaf(Node):
    pass


x = Leaf()
x.add(Node())
"""
SELF_MSG = 'Argument 1 to "add" of "Node" has incompatible type "Node"; expected "Leaf"'
ATTR_SRC = (EXAMPLES / "self_param_unsound.py").read_text()
PRINT_LINE = next(i for i, ln in enumerate(ATTR_SRC.splitlines(), 1) if ln.startswith("print("))


def diag(tool, line, code, msg="m", sev=Severity.ERROR, rev=None, col=1):
    return Diagnostic(tool, line, col, sev, code, msg, revealed_type=rev)


def offline_state(source, diags=None, runtime=None, runners=None):
    return CaseState("t", source, "3.12", diags or {Tool.MYPY: [], Tool.TY: []},
                     runtime or RuntimeResult(status="success"), [], {}, {}, runners=runners)


def self_case(src=SELF_SRC, msg=SELF_MSG, line=14, runtime=None, runners=None, kind=Tool.MYPY):
    st = offline_state(src, {Tool.MYPY: [diag(Tool.MYPY, line, "arg-type", msg, col=7)] if kind == Tool.MYPY else [],
                             Tool.TY: [] if kind == Tool.MYPY else [diag(Tool.TY, line, "invalid-argument-type", msg, col=7)]},
                       runtime, runners)
    ds = find_discrepancies(st.diags, st.amap, st.runtime)
    return st, next(d for d in ds if d.kind in (K.ONLY_MYPY, K.ONLY_TY))


class FakeRunners:
    """Canned checker answers. Knobs: what the spec-desugared variant and the LSP probe look like to the tool."""

    def __init__(self, variant_diag=False, fail_variant=False, lsp_rejects=False, runtime=None):
        self.variant_diag, self.fail_variant, self.lsp_rejects = variant_diag, fail_variant, lsp_rejects
        self.runtime = runtime or RuntimeResult(status="success")

    def available(self, tool):
        return True

    def version(self, tool):
        return "fake"

    def run_runtime(self, src):
        return self.runtime

    def check(self, tool, src, flags=None):
        diags = []
        lines = src.splitlines()
        if "_TdSelf" in src and tool == Tool.TY:
            if self.fail_variant:
                return CheckResult(ToolRun(tool, "", "error: boom", 2), [], [])
            if self.variant_diag:
                diags.append(diag(tool, lines.index("x.add(Node())") + 1, "invalid-argument-type", "rejects", col=7))
        if "_td_lsp_probe" in src and tool == Tool.MYPY and self.lsp_rejects:
            diags.append(diag(tool, lines.index("    n.add(Node())") + 1, "arg-type", "rejects", col=7))
        return CheckResult(ToolRun(tool, "", "", 1 if diags else 0), diags, [])


# --------------------------------------------------------------------------- (b) SELF_CONTRADICTION demotion


class OracleEx:
    """Stands in for the experiment runner inside call_assignability_oracle."""

    def __init__(self, sig, assign_line):
        self.sig, self.assign_line = sig, assign_line

    def run(self, d, req):
        if req["kind"] == "reveal_probe":
            return ExperimentResult("E1", "reveal_probe", req, True, "", {req["exprs"][0]: {"ty": self.sig}})
        return ExperimentResult("E2", "assignability", req, True, "", {
            "ty": [f"L{self.assign_line}:19 error[invalid-assignment] not assignable"]})


def _oracle(src, line, msg, sig):
    st = offline_state(src, {Tool.MYPY: [diag(Tool.MYPY, line, "arg-type", msg, col=col_of(src, line))], Tool.TY: []})
    d = find_discrepancies(st.diags, st.amap, st.runtime)[0]
    return call_assignability_oracle(st, d, OracleEx(sig, line))


def col_of(src, line):
    text = src.splitlines()[line - 1]
    return text.index("(") + 2  # first character of the single argument


def test_reveal_only_contradiction_on_a_self_method_is_weak():
    ev = _oracle(SELF_SRC, 14, SELF_MSG, "bound method Leaf.add(c: Leaf) -> Leaf")
    assert ev is not None and ev.type == EvidenceType.SELF_CONTRADICTION and ev.supports == "bug"
    assert ev.strength == "weak" and "display" in ev.summary


def test_call_vs_declared_signature_contradiction_stays_strong():
    src = "def f(x: int) -> int:\n    return x\n\n\nf('a')\n"
    ev = _oracle(src, 5, 'Argument 1 to "f" has incompatible type "str"; expected "int"', "def f(x: int) -> int")
    assert ev is not None and ev.strength == "strong"


def test_display_sensitivity_helper():
    import ast

    tree = ast.parse("from typing import Self, TypeVar\nT = TypeVar('T')\nclass A:\n    def m(self, c: Self): ...\n"
                     "    def n(self, c: int): ...\ndef g(x: T) -> T: ...\ndef h(x: int) -> int: ...\n")
    call = lambda s: ast.parse(s, mode="eval").body.func  # noqa: E731
    assert reveal_is_display_sensitive(tree, call("a.m(1)"), "(c: A) -> None")  # Self parameter, printed specialised
    assert reveal_is_display_sensitive(tree, call("g(1)"), "(x: int) -> int")  # TypeVar parameter
    assert not reveal_is_display_sensitive(tree, call("a.n(1)"), "(c: int) -> None")
    assert not reveal_is_display_sensitive(tree, call("h(1)"), "(x: int) -> int")


def _bug(strength, etype=EvidenceType.SELF_CONTRADICTION):
    return Finding("D1", Verdict.BUG, Tier.REVIEW, "ty", None, None, 0.95, "llm",
                   evidence=[Evidence(etype, "bug", "s", verified=True, strength=strength)], review_notes=["SKEPTIC:AGREE: ok"])


def test_weak_self_contradiction_cannot_make_a_bug_tier():
    adj = Adjudicator(CachedLLM(NullLLM()), Corpus())
    assert adj.gate(_bug("weak")).tier == Tier.REVIEW
    assert adj.gate(_bug("strong")).tier == Tier.CONFIRMED  # control: call-vs-call evidence still confirms


@needs_tools
def test_self_example_lands_in_review_with_weak_evidence_only():
    p = Pipeline(PipelineConfig(reduce=False, audit_rate=0.0, use_pyright=False), llm=CachedLLM(NullLLM()))
    rep = p.run_source(ATTR_SRC, "self-example")
    assert rep.findings and all(f.tier == Tier.REVIEW for f in rep.findings)
    sc = [e for f in rep.findings for e in f.evidence if e.type == EvidenceType.SELF_CONTRADICTION]
    assert sc and all(e.strength == "weak" for e in sc)


# --------------------------------------------------------------------------- (a) the KB entry


def test_matcher_fires_on_the_narrow_pattern():
    st, d = self_case()
    assert "TY-SELF-UPPER-BOUND" in [e.id for e in matching_entries(st, d)]


@pytest.mark.parametrize("src,msg", [
    # keyword argument form
    (SELF_SRC.replace("x.add(Node())", "x.add(c=Node())"), 'Argument "c" to "add" of "Node" has incompatible type "Node"; expected "Leaf"'),
    # Self nested in a container
    (SELF_SRC.replace("c: Self", "c: list[Self]").replace("x.add(Node())", "x.add([Node()])"),
     'Argument 1 to "add" of "Node" has incompatible type "list[Node]"; expected "list[Leaf]"'),
    # generic base specialised by the subclass
    ("from typing import Self\n\n\nclass Box[T]:\n    def merge(self, other: Self) -> Self:\n        return self\n\n\n"
     "class IntBox(Box[int]):\n    pass\n\n\nx = IntBox()\nx.merge(Box[int]())\n",
     'Argument 1 to "merge" of "Box" has incompatible type "Box[int]"; expected "IntBox"'),
])
def test_matcher_variants(src, msg):
    st, d = self_case(src, msg)
    assert "TY-SELF-UPPER-BOUND" in [e.id for e in matching_entries(st, d)]


@pytest.mark.parametrize("name,src,msg", [
    ("override in between", SELF_SRC.replace("class Leaf(Node):\n    pass", "class Leaf(Node):\n    def add(self, c: Self) -> Self:\n        return self"),
     SELF_MSG),
    ("Self only in receiver and return", SELF_SRC.replace("c: Self", "c: int"), SELF_MSG),
    ("expected type is not a subclass of the definer", SELF_SRC, 'Argument 1 to "add" of "Node" has incompatible type "Node"; expected "Other"'),
    ("rejected argument unrelated to the receiver", SELF_SRC.replace("class Leaf", "class Other:\n    pass\n\n\nclass Leaf"),
     'Argument 1 to "add" of "Node" has incompatible type "Other"; expected "Leaf"'),
    ("a different rejection", SELF_SRC, 'Unsupported operand types for + ("Node" and "Leaf")'),
])
def test_matcher_does_not_fire_outside_the_pattern(name, src, msg):
    line = 14 + (src.count("\n") - SELF_SRC.count("\n"))
    st, d = self_case(src, msg, line=line)
    assert "TY-SELF-UPPER-BOUND" not in [e.id for e in matching_entries(st, d)], name


def test_matcher_ignores_ty_side_rejections():
    st, d = self_case(kind=Tool.TY)
    assert d.kind == K.ONLY_TY and "TY-SELF-UPPER-BOUND" not in [e.id for e in matching_entries(st, d)]


def test_entry_is_hint_only_until_the_desugar_probe_confirms():
    # offline: no experiment can run -> the entry is a hint, nothing is dismissed
    st, d = self_case()
    decided, remaining = deterministic_stage(st, [d], ExperimentRunner(st), auto_probe=False)
    assert not decided and remaining == [d] and "TY-SELF-UPPER-BOUND" in d.kb_hits
    # online, the answer is unchanged under the spec's desugaring -> dismissed, citing the entry and its experiment
    st, d = self_case(runners=FakeRunners())
    decided, _ = deterministic_stage(st, [d], ExperimentRunner(st), auto_probe=False)
    f = decided["D1"]
    assert f.decided_by == "kb:TY-SELF-UPPER-BOUND" and f.tier == Tier.DISMISSED
    assert any(e.type == EvidenceType.EXPERIMENT and "desugaring" in e.summary for e in f.evidence)
    # online, the answer CHANGES under the desugaring -> the explanation does not apply -> stays in review
    st, d = self_case(runners=FakeRunners(variant_diag=True))
    decided, remaining = deterministic_stage(st, [d], ExperimentRunner(st), auto_probe=False)
    assert not decided and remaining == [d]
    # online, the desugared run FAILS -> inconclusive, never a dismissal
    st, d = self_case(runners=FakeRunners(fail_variant=True))
    decided, remaining = deterministic_stage(st, [d], ExperimentRunner(st), auto_probe=False)
    assert not decided and remaining == [d]


CRASH = RuntimeResult(status="exception", exc_type="AttributeError", exc_message="'Node' object has no attribute 'leaf_only'",
                      exc_line=17, frames=[(17, "<module>")], executed_lines=[14, 15, 16, 17])
ATTR_STATE_SRC = SELF_SRC.replace("class Node:\n", "class Node:\n    nxt: list[Self]\n\n") + "print(x.nxt[0].leaf_only())\n"


def test_self_typed_state_crash_is_not_dismissed_but_explained():
    # SELF_SRC has no Self-typed state: the crash alone must not demote the entry (control)
    st, d = self_case(runtime=CRASH, runners=FakeRunners())
    assert entry_demotion(st, d, BY_ID["TY-SELF-UPPER-BOUND"]) is None
    # with a list[Self] attribute AND a CPython type exception the entry steps aside, even though the probe would confirm
    st, d = self_case(ATTR_STATE_SRC, line=16, runtime=CRASH, runners=FakeRunners())
    dem = entry_demotion(st, d, BY_ID["TY-SELF-UPPER-BOUND"])
    assert dem is not None and dem.supports == "neutral" and "Self-typed attribute" in dem.summary
    decided, remaining = deterministic_stage(st, [d], ExperimentRunner(st), auto_probe=False)
    assert not decided and remaining == [d]
    assert any("Self-typed attribute" in e.summary for e in d.evidence)
    assert not kb_entry_eligible(st, d, BY_ID["TY-SELF-UPPER-BOUND"])


def test_self_typed_state_means_attributes_not_locals():
    import ast

    from typediff.selfparam import has_self_typed_state

    pre = "from typing import Self\n"
    assert has_self_typed_state(ast.parse(pre + "class A:\n    nxt: Self | None = None\n"))
    assert has_self_typed_state(ast.parse(pre + "class A:\n    def __init__(self) -> None:\n        self.kids: list[Self] = []\n"))
    assert not has_self_typed_state(ast.parse(pre + "class A:\n    def m(self) -> None:\n        y: Self = self\n"))
    assert not has_self_typed_state(ast.parse(pre + "class A:\n    def m(self, c: Self) -> Self:\n        return self\n"))


@needs_tools
def test_real_tools_self_example_and_kb_selftest_program():
    p = Pipeline(PipelineConfig(reduce=False, audit_rate=0.0, use_pyright=False), llm=CachedLLM(NullLLM()))
    ok = p.run_source(BY_ID["TY-SELF-UPPER-BOUND"].example, "kb-self")
    assert any(f.decided_by == "kb:TY-SELF-UPPER-BOUND" for f in ok.findings)
    rep = p.run_source(ATTR_SRC, "self-attr")
    d1 = next(f for f in rep.findings if f.discrepancy_id == "D1")
    assert d1.tier == Tier.REVIEW and "TY-SELF-UPPER-BOUND" in next(d for d in rep.discrepancies if d.id == "D1").kb_hits


# --------------------------------------------------------------------------- (c) spec_desugar


def test_desugar_unchanged_answer_is_consistent_with_the_spec_and_never_a_dismissal():
    st, d = self_case(runners=FakeRunners())
    res = ExperimentRunner(st).spec_desugar(d, {"kind": "spec_desugar"})
    assert res.ok and res.outcome["unchanged"] is True and res.outcome["tool"] == "ty"
    assert "consistent with the spec's own desugaring" in res.summary
    assert res.evidence.supports == "neutral" and res.evidence.strength == "weak"  # NOT dismissal evidence by itself
    assert "_TdSelf_Node" in res.outcome["variant_source"] and "self: _TdSelf_Node" in res.outcome["variant_source"]
    assert "c: _TdSelf_Node" in res.outcome["variant_source"] and "bound='Node'" in res.outcome["variant_source"]


def test_desugar_changed_answer_is_reported():
    st, d = self_case(runners=FakeRunners(variant_diag=True))
    res = ExperimentRunner(st).spec_desugar(d, {"kind": "spec_desugar"})
    assert res.ok and res.outcome["unchanged"] is False and "CHANGES" in res.summary
    assert "consistent with the spec" not in res.evidence.summary


def test_desugar_failed_run_is_inconclusive():
    st, d = self_case(runners=FakeRunners(fail_variant=True))
    res = ExperimentRunner(st).run(d, {"kind": "spec_desugar"})
    assert not res.ok and res.evidence is None and "inconclusive" in res.summary


def test_desugar_rejects_unsupported_shapes():
    st, d = self_case("class A:\n    def m(self, c: int) -> int:\n        return c\n\n\nA().m(1)\n",
                      'Argument 1 to "m" of "A" has incompatible type "str"; expected "int"', line=6, runners=FakeRunners())
    res = ExperimentRunner(st).run(d, {"kind": "spec_desugar", "class": "A"})
    assert not res.ok and "no instance method with Self" in res.summary


@needs_tools
def test_desugar_with_real_ty_gives_the_same_answer():
    runners = Runners(ToolConfig())
    st = offline_state(SELF_SRC, runners=runners)
    for t in (Tool.MYPY, Tool.TY):
        st.diags[t] = runners.check(t, SELF_SRC).diagnostics
    st.runtime = runners.run_runtime(SELF_SRC)
    d = next(x for x in find_discrepancies(st.diags, st.amap, st.runtime) if x.kind == K.ONLY_MYPY)
    res = ExperimentRunner(st).spec_desugar(d, {"kind": "spec_desugar"})
    assert res.ok and res.outcome["unchanged"] is True


# --------------------------------------------------------------------------- (d) LSP probe


def test_lsp_probe_downgrades_a_reading_that_is_not_liskov_safe():
    st, d = self_case(runners=FakeRunners())
    res = ExperimentRunner(st).lsp_probe(d, {"kind": "lsp_probe"})
    assert res.ok and res.outcome["accepts_base_call"] and res.outcome["accepts_sub_call"]
    assert "def _td_lsp_probe(n: Node)" in res.outcome["probe_source"] and "_td_lsp_probe(Leaf())" in res.outcome["probe_source"]
    assert res.evidence.type == EvidenceType.CONSENSUS and res.evidence.strength == "weak"
    assert res.evidence.supports == "neutral" and "CONSENSUS-downgrade" in res.evidence.summary


def test_lsp_probe_no_downgrade_when_the_tool_rejects_the_probe_too():
    st, d = self_case(runners=FakeRunners(lsp_rejects=True))
    res = ExperimentRunner(st).lsp_probe(d, {"kind": "lsp_probe"})
    assert res.ok and res.evidence is None and not res.outcome["accepts_base_call"]


def test_lsp_probe_is_narrow_and_fail_closed():
    st, d = self_case(SELF_SRC, 'Unsupported operand types for + ("Node" and "Leaf")', runners=FakeRunners())
    assert not ExperimentRunner(st).run(d, {"kind": "lsp_probe"}).ok  # not the Self-parameter pattern
    st, d = self_case(runners=FakeRunners())
    st.runners.check = lambda tool, src, flags=None: CheckResult(ToolRun(tool, "", "boom", 2), [], [])
    res = ExperimentRunner(st).run(d, {"kind": "lsp_probe"})
    assert not res.ok and res.evidence is None and "inconclusive" in res.summary


def test_lsp_downgrade_note_reaches_the_discrepancy_evidence():
    st, d = self_case(runners=FakeRunners())
    deterministic_stage(st, [d], ExperimentRunner(st), auto_probe=False)
    assert any(e.type == EvidenceType.CONSENSUS and "CONSENSUS-downgrade" in e.summary for e in d.evidence)


# --------------------------------------------------------------------------- (e) prior stance


def test_priors_registered_and_schema_valid():
    import json

    data = json.loads(priors_mod.PATH.read_text())
    ids = {p["id"] for p in data["prior_stances"]} | {e["id"] for e in data["entries"] if e.get("stance")}
    assert {"TY-4656", "TY-4673", "TY-1172", "TY-2255"} <= ids
    for p in data["prior_stances"] + [e for e in data["entries"] if e.get("stance")]:
        assert p["stance"] in priors_mod.STANCES and p["url"].startswith("https://")


def test_prior_stance_found_by_tags_and_by_signature():
    st, d = self_case()
    hits = {p.id: p for p in find_priors(SELF_SRC, d)}
    assert {"TY-4656", "TY-1172"} <= set(hits) and hits["TY-4656"].stance == "intended"
    assert hits["TY-4656"].url == "https://github.com/astral-sh/ty/issues/4656"
    # signature path (no feature tag needed): a bound-method reveal mismatch on a Self/TypeVar program
    src = "from typing import TypeVar\nT = TypeVar('T')\nx = 1\n"
    other = Discrepancy("D9", K.REVEAL_MISMATCH, 3, 3, "x = 1", "",
                        ty=[diag(Tool.TY, 3, None, "Revealed type", rev="bound method A.m(c: A) -> A")])
    assert [p.id for p in find_priors(src, other)] == ["TY-4673"]


def test_prior_stance_does_not_match_unrelated_findings():
    src = "x: int = 'a'\n"
    d = Discrepancy("D1", K.ONLY_MYPY, 1, 1, "x: int = 'a'", "", mypy=[diag(Tool.MYPY, 1, "assignment", "Incompatible types")])
    assert find_priors(src, d) == [] and find_priors(src, None) == []


def test_prior_cap_only_lowers_confirmed_and_candidate():
    pr = find_priors(SELF_SRC, self_case()[1])
    for tier, expected in ((Tier.CONFIRMED, Tier.REVIEW), (Tier.CANDIDATE, Tier.REVIEW), (Tier.REVIEW, Tier.REVIEW),
                           (Tier.DISMISSED, Tier.DISMISSED)):
        f = Finding("D1", Verdict.BUG, tier, "ty", None, None, 0.9, "llm")
        assert apply_prior_cap(f, pr) and f.tier == expected
        assert any("body text on the tracker" in n and "ty/issues/4656" in n for n in f.review_notes)
        apply_prior_cap(f, pr)
        assert len([n for n in f.review_notes if n.startswith("PRIOR-STANCE")]) == 1  # idempotent


def test_pipeline_caps_a_confirmed_bug_with_a_prior_but_not_an_unrelated_one():
    p = Pipeline(PipelineConfig(reduce=False, audit_rate=0.0, use_pyright=False), llm=CachedLLM(NullLLM()))

    def confirm(state, ds, ex, known):
        return {d.id: Finding(d.id, Verdict.BUG, Tier.CONFIRMED, "ty", None, None, 0.95, "llm") for d in ds}

    p.adjudicator.adjudicate = confirm
    rep = p.judge_logs(SELF_SRC, f"case.py:14:7: error: {SELF_MSG}  [arg-type]\n", "", "ok")
    f = rep.findings[0]
    assert f.tier == Tier.REVIEW and any(n.startswith("PRIOR-STANCE") for n in f.review_notes)
    rep = p.judge_logs("x: int = 'a'\n", "case.py:1:10: error: Incompatible types in assignment  [assignment]\n", "", "ok")
    assert rep.findings[0].tier == Tier.CONFIRMED  # control: no prior, nothing capped


def _report(f, d, src, evidence_runtime=False):
    return CaseReport("c", src, "3.12", {"ty": "ty"}, {}, {"mypy": d.mypy, "ty": d.ty}, RuntimeResult(status="success"), [], [d], [f], {})


def test_draft_issue_consults_priors_and_warns():
    st, d = self_case()
    f = Finding("D1", Verdict.BUG, Tier.CONFIRMED, "ty", None, None, 0.95, "llm", correct_behavior="reject")
    text = draft_issue(_report(f, d, SELF_SRC), f)
    assert f.tier == Tier.REVIEW  # capped before drafting
    assert "do not file yet" in text and "ty/issues/4656" in text and "body text" in text
    other = Discrepancy("D1", K.ONLY_MYPY, 1, 1, "x: int = 'a'", "", mypy=[diag(Tool.MYPY, 1, "assignment", "Incompatible")])
    g = Finding("D1", Verdict.BUG, Tier.CONFIRMED, "ty", None, None, 0.95, "llm")
    assert "do not file yet" not in draft_issue(_report(g, other, "x: int = 'a'\n"), g) and g.tier == Tier.CONFIRMED


# --------------------------------------------------------------------------- (f) runtime evidence and the reducer


def test_runtime_evidence_names_the_responsible_constructs():
    st = offline_state(ATTR_SRC, runtime=RuntimeResult(
        status="exception", exc_type="AttributeError", exc_message="'Node' object has no attribute 'leaf_only'",
        exc_line=PRINT_LINE, frames=[(PRINT_LINE, "<module>")], executed_lines=[PRINT_LINE]))
    d = Discrepancy("D2", K.RUNTIME_MISS, PRINT_LINE, PRINT_LINE, "print(x.children[0].leaf_only())", "")
    attach_runtime_evidence(st, d)
    (ev,) = [e for e in d.evidence if e.supports == "bug"]
    assert "attribute `children: list[Self]`" in ev.summary and "method `leaf_only`" in ev.summary


class LostRuntime:
    def run_runtime(self, src):
        return RuntimeResult(status="success")


def test_reducer_says_so_when_the_runtime_failure_is_lost_and_the_draft_does_not_claim_a_crash():
    st = offline_state(ATTR_SRC, runtime=RuntimeResult(
        status="exception", exc_type="AttributeError", exc_message="'Node' object has no attribute 'leaf_only'",
        exc_line=PRINT_LINE, frames=[(PRINT_LINE, "<module>")], executed_lines=[PRINT_LINE]), runners=LostRuntime())
    crash_ev = Evidence(EvidenceType.RUNTIME, "bug", "CPython raised AttributeError ...", verified=True, strength="strong")
    f = Finding("D1", Verdict.BUG, Tier.CONFIRMED, "ty", None, None, 0.95, "llm", evidence=[crash_ev])
    reduced = "from typing import Self\n\n\nclass Node:\n    def add(self, c: Self) -> Self:\n        return self\n"
    Pipeline(PipelineConfig(), llm=CachedLLM(NullLLM()))._check_runtime_kept(st, f, reduced)
    (note,) = [n for n in f.review_notes if n.startswith("REDUCER:RUNTIME-LOST")]
    assert "does NOT raise AttributeError" in note and "leaf_only" in note
    d = Discrepancy("D1", K.ONLY_MYPY, 23, 23, "x.add(Node())", "", mypy=[diag(Tool.MYPY, 23, "arg-type", "m")])
    text = draft_issue(_report(f, d, ATTR_SRC), f)
    assert "CPython raised" not in text and "does NOT reproduce the CPython failure" in text
    f2 = Finding("D1", Verdict.BUG, Tier.CONFIRMED, "mypy", None, None, 0.95, "llm", evidence=[crash_ev])
    assert "CPython raised" in draft_issue(_report(f2, d, "x = 1\n"), f2)  # control: no loss recorded -> claim kept


@needs_tools
def test_reducer_keeps_the_statement_and_attribute_that_make_it_crash():
    runners = Runners(ToolConfig())
    diags = {t: runners.check(t, ATTR_SRC).diagnostics for t in (Tool.MYPY, Tool.TY)}
    st = CaseState("t", ATTR_SRC, "3.12", diags, runners.run_runtime(ATTR_SRC), [], {}, {}, runners=runners)
    d = next(x for x in find_discrepancies(st.diags, st.amap, st.runtime) if x.kind == K.RUNTIME_MISS)
    attach_runtime_evidence(st, d)
    f = Finding(d.id, Verdict.BUG, Tier.CANDIDATE, "both", None, None, 0.9, "llm", evidence=list(d.evidence))
    red = Reducer(runners, st.module, 40)
    pred = red.predicate_for(ATTR_SRC, d, f, runtime=st.runtime)
    assert pred(ATTR_SRC)
    real = runners.run_runtime
    same_stmt = [(PRINT_LINE, "<module>")]
    try:  # still an AttributeError at the same statement, but for ANOTHER reason (the attribute was dropped)
        runners.run_runtime = lambda src: RuntimeResult(
            status="exception", exc_type="AttributeError", exc_message="'Leaf' object has no attribute 'children'",
            exc_line=PRINT_LINE, frames=same_stmt, executed_lines=[PRINT_LINE])
        assert not pred(ATTR_SRC)
        # the same exception class and message, but raised by a different statement
        runners.run_runtime = lambda src: RuntimeResult(
            status="exception", exc_type="AttributeError", exc_message=st.runtime.exc_message, exc_line=PRINT_LINE - 1,
            frames=[(PRINT_LINE, "<module>")], executed_lines=[PRINT_LINE])
        assert not pred(ATTR_SRC)
    finally:
        runners.run_runtime = real
    from typediff.anchors import statement_key

    reduced = red.reduce(ATTR_SRC, pred, statement_key(st.amap.stmt(d.anchor).node))
    again = runners.run_runtime(reduced)
    assert "children" in reduced and "leaf_only" in reduced
    assert (again.exc_type, again.exc_message) == (st.runtime.exc_type, st.runtime.exc_message)


# --------------------------------------------------------------------------- (g) leftover review items


def test_precision_entry_uses_the_paired_probe():
    src = "for i in range(3):\n    reveal_type(i)\n"
    shape = lambda v: {"type": "int", "mro": ["int", "object"], "repr": str(v)}  # noqa: E731
    mk = lambda n: RuntimeResult(status="success", probes=[RuntimeProbe(2, shape(i)) for i in range(n)], executed_lines=[1, 2])  # noqa: E731
    diags = {Tool.MYPY: [diag(Tool.MYPY, 2, None, rev="builtins.object", sev=Severity.NOTE)],
             Tool.TY: [diag(Tool.TY, 2, "revealed-type", rev="int", sev=Severity.NOTE)]}
    st = offline_state(src, diags, mk(1))
    d = find_discrepancies(st.diags, st.amap, st.runtime)[0]
    d.reveal_relation = "ty_more_precise"
    assert m_precision_runtime_consistent(st, d)  # control: one reveal, one probe, the value inhabits the precise type
    st = offline_state(src, diags, mk(3))
    assert not m_precision_runtime_consistent(st, d)  # three probes for one reveal: ambiguous -> adjudicate, not dismiss


def test_pyright_abnormal_exit_is_capped_like_mypy_and_ty():
    for tool in (Tool.MYPY, Tool.TY, Tool.PYRIGHT):
        (f,) = crash_findings([Crash(tool, "abnormal_exit", f"{tool.value}:exit2", "usage", 2)])
        assert f.tier == Tier.REVIEW and f.verdict == Verdict.NEEDS_HUMAN
    (f,) = crash_findings([Crash(Tool.PYRIGHT, "internal_error", "pyright:boom", "trace", 1)])
    assert f.tier == Tier.CONFIRMED  # control: a real crash is still a confirmed finding


def _toggle_result(flag, persists, d_id="D1"):
    req = {"kind": "config_toggle", "tool": "ty", "flags": ["--config", flag]}
    return ExperimentResult("E7", "config_toggle", req, True, "x", {"persists": persists},
                            Evidence(EvidenceType.EXPERIMENT, "neutral" if persists else "not_bug", "x", verified=True), d_id)


def test_verify_required_entry_needs_its_own_toggle():
    d = Discrepancy("D1", K.ONLY_MYPY, 1, 1, "x", "", mypy=[diag(Tool.MYPY, 1, "x")])
    st = offline_state("x = 1\n")
    eq, gen = BY_ID["TY-STRICT-EQUALITY"], BY_ID["TY-GRADUAL-GENERIC-NARROWING"]

    def ex_with(*results):
        ex = ExperimentRunner(st)
        ex.results.extend(results)
        return ex

    other = ex_with(_toggle_result("analysis.strict-generic-narrowing=true", False))  # the OTHER entry's toggle
    assert not kb_entry_eligible(st, d, eq, other) and kb_entry_eligible(st, d, gen, other)
    own = ex_with(_toggle_result("analysis.strict-equality-semantics=true", False))
    assert kb_entry_eligible(st, d, eq, own) and not kb_entry_eligible(st, d, gen, own)
    persists = ex_with(_toggle_result("analysis.strict-equality-semantics=true", True))
    assert not kb_entry_eligible(st, d, eq, persists)  # the discrepancy survived its own toggle
    assert not kb_entry_eligible(st, d, eq, ex_with(_toggle_result("analysis.strict-equality-semantics=true", False, "D2")))
    assert not kb_entry_eligible(st, d, eq)  # no experiments at all
    # an unrelated verified not_bug EXPERIMENT in d.evidence (the old, too-lax condition) is not enough
    d.evidence.append(Evidence(EvidenceType.EXPERIMENT, "not_bug", "something else", verified=True))
    assert not kb_entry_eligible(st, d, eq, other)
