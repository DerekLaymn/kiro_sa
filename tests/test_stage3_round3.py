"""Stage 3 round 3: stale-alias guard for MYPY-13807-ALIASED-CONDITIONS (reviewer issue 3 of round 2), further entries below."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from typediff.calibration import classify, must_stay_live, summarize
from typediff.kb import BY_ID, matching_entries
from typediff.llm import CachedLLM, NullLLM
from typediff.models import Diagnostic, Discrepancy, DiscrepancyKind as K, RuntimeResult, Severity, Tier, Tool
from typediff.pipeline import Pipeline, PipelineConfig
from typediff.state import CaseState

BIN = Path(sys.executable).parent
needs_tools = pytest.mark.skipif(not ((BIN / "mypy").exists() and (BIN / "ty").exists()), reason="mypy/ty not installed")
ROOT = Path(__file__).resolve().parents[1]

AID = "MYPY-13807-ALIASED-CONDITIONS"


def alias_case(src, line, col, rel_name="ty_more_precise"):
    ty = Diagnostic(Tool.TY, line, col, Severity.NOTE, "revealed-type", "", revealed_type="None")
    my = Diagnostic(Tool.MYPY, line, col, Severity.NOTE, None, "", revealed_type="int | None")
    st = CaseState("t", src, "3.13", {Tool.MYPY: [my], Tool.TY: [ty], Tool.PYRIGHT: []}, RuntimeResult(status="success"), [], {}, {})
    return st, Discrepancy("D1", K.REVEAL_MISMATCH, line, line, "s", "", mypy=[my], ty=[ty], reveal_relation=rel_name)


def ahit(st, d):
    return AID in {e.id for e in matching_entries(st, d)}

ATTR = "class A:\n    x: int | None\n\ndef f(a: A) -> None:\n    is_none = a.x is None\n{mid}    if not is_none:\n        reveal_type(a.x)\n"


def attr_case(mid):
    src = ATTR.format(mid=mid)
    line = src.count("\n", 0, src.index("reveal_type")) + 1
    return alias_case(src, line, 21)


def test_unchanged_target_is_still_dismissed():
    assert ahit(*attr_case(""))
    assert ahit(*attr_case("    print('between')\n"))  # a call that does not mention the aliased root


@pytest.mark.parametrize("mid", [
    "    a.x = 1\n",  # store into the target
    "    a.x += 1\n",
    "    a = A()\n",  # root rebound
    "    a.clear()\n",  # method call on the root (reviewer's program)
    "    g(a)\n",  # root passed to a call
    "    for a in []:\n        pass\n",
    "    (a := A())\n",
    "    del a.x\n",
])
def test_stale_alias_stays_in_review(mid):
    assert not ahit(*attr_case(mid))


def test_stale_alias_plain_name_and_subscript():
    plain = "def f(x: int | None) -> None:\n    is_none = x is None\n{mid}    if is_none:\n        reveal_type(x)\n"
    assert ahit(*alias_case(plain.format(mid=""), 4, 21))
    assert ahit(*alias_case(plain.format(mid="    print(x)\n"), 5, 21))  # a call cannot rebind a plain name
    assert not ahit(*alias_case(plain.format(mid="    x = None\n"), 5, 21))
    assert not ahit(*alias_case(plain.format(mid="    x: int | None = 3\n"), 5, 21))
    sub = "def f(l: list[int | None]) -> None:\n    is_none = l[0] is None\n{mid}    if is_none:\n        reveal_type(l[0])\n"
    assert ahit(*alias_case(sub.format(mid=""), 4, 21))
    assert not ahit(*alias_case(sub.format(mid="    l[0] = 1\n"), 5, 21))
    assert not ahit(*alias_case(sub.format(mid="    l.clear()\n"), 5, 21))


def test_store_after_the_if_or_in_another_scope_is_not_between():
    src = "def f(x: int | None) -> None:\n    is_none = x is None\n    if is_none:\n        reveal_type(x)\n    x = 3\n"
    assert ahit(*alias_case(src, 4, 21))


def pipeline():
    return Pipeline(PipelineConfig(reduce=False, audit_rate=0.0, use_pyright=False), llm=CachedLLM(NullLLM()))


@needs_tools
def test_stale_alias_program_stays_in_review_with_real_tools():
    src = (ROOT / "calibration" / "must_stay_live" / "mypy_stale_alias.py").read_text()
    rep = pipeline().run_source(src, "stale-alias")
    assert rep.findings and not any(f.tier == Tier.DISMISSED for f in rep.findings), [(f.decided_by, f.tier) for f in rep.findings]


# ---------------------------------------------------------------- calibration negatives that close without pyright


@needs_tools
def test_error_recovery_example_and_negative_close_without_pyright():
    for src in (BY_ID["REVEAL-ERROR-RECOVERY"].example, (ROOT / "calibration" / "negatives" / "reveal_error_recovery.py").read_text()):
        rep = pipeline().run_source(src, "recovery-neg")
        assert rep.findings and all(f.tier == Tier.DISMISSED for f in rep.findings), [(f.decided_by, f.tier) for f in rep.findings]
        assert any(f.decided_by == "kb:REVEAL-ERROR-RECOVERY" for f in rep.findings)


# ---------------------------------------------------------------- calibrate reports must-stay-live programs that get dismissed


class _F:
    def __init__(self, tier):
        self.tier = tier


class _R:
    def __init__(self, *tiers):
        self.findings = [_F(t) for t in tiers]


def test_must_stay_live_loader_and_classification(tmp_path):
    (tmp_path / "b.py").write_text("x = 1\n")
    (tmp_path / "a.py").write_text("y = 2\n")
    cases = must_stay_live(tmp_path)
    assert [c["id"] for c in cases] == ["live-a", "live-b"] and all(c["kind"] == "must_stay_live" for c in cases)
    assert must_stay_live(tmp_path / "missing") == []
    c = cases[0]
    assert classify(c, _R(Tier.REVIEW)) == "live"
    assert classify(c, _R(Tier.REVIEW, Tier.DISMISSED)) == "violated"  # one dismissed finding is enough
    assert classify(c, _R(Tier.DISMISSED)) == "violated"
    assert classify(c, _R()) == "invisible"
    # a positive with the same findings is only a false dismissal when ALL of them are dismissed
    assert classify({"kind": "positive", "source": "x"}, _R(Tier.REVIEW, Tier.DISMISSED)) == "kept"


def test_summary_lists_dismissed_must_stay_live_programs():
    rows = [{"id": "live-a", "kind": "must_stay_live", "outcome": "live", "findings": []},
            {"id": "live-b", "kind": "must_stay_live", "outcome": "violated", "findings": []},
            {"id": "ty-1", "kind": "positive", "outcome": "kept", "findings": [], "url": ""}]
    s = summarize(rows)
    assert s["must_stay_live"] == 2 and s["must_stay_live_dismissed"] == ["live-b"]
    assert s["must_stay_live_outcomes"] == {"live": 1, "violated": 1}
    assert s["positives"] == 1 and s["negatives"] == 0  # the new kind does not leak into the other metrics


# ---------------------------------------------------------------- NameError policy: one answer in both code paths + hint

NAME_SRC = "x: int\nprint(x)\n"
NAME_RT = dict(status="exception", exc_type="NameError", exc_message="name 'x' is not defined", exc_line=2,
               frames=[(2, "<module>")], executed_lines=[1, 2])


def name_case(mypy=(), ty=()):
    from typediff.discrepancy import find_discrepancies

    st = CaseState("t", NAME_SRC, "3.13", {Tool.MYPY: list(mypy), Tool.TY: list(ty), Tool.PYRIGHT: []},
                   RuntimeResult(**NAME_RT), [], {}, {})
    return st, next(x for x in find_discrepancies(st.diags, st.amap, st.runtime) if x.kind in (K.ONLY_TY, K.ONLY_MYPY))


def test_both_code_paths_treat_a_nameerror_as_strong_and_blame_the_silent_tool():
    from typediff.kb import runtime_contradiction
    from typediff.rules import attach_runtime_evidence

    ty = Diagnostic(Tool.TY, 2, 1, Severity.ERROR, "unresolved-reference", "Name `x` used when not defined")
    st, d = name_case(ty=[ty])
    assert runtime_contradiction(st, d) is not None  # kb path: strong
    attach_runtime_evidence(st, d)  # rules path: strong, blames mypy (never ty)
    strong = [e for e in d.evidence if e.supports == "bug" and e.strength == "strong"]
    assert len(strong) == 1 and strong[0].blame == "mypy"
    assert not any(e.blame == "ty" for e in d.evidence)


def test_nameerror_policy_does_not_stop_the_tracked_limitation_entries_from_dismissing():
    from typediff.kb import entry_demotion

    ty = Diagnostic(Tool.TY, 2, 1, Severity.ERROR, "unresolved-reference", "Name `x` used when not defined")
    st, d = name_case(ty=[ty])
    # ANNOTATION-ONLY-READ keeps runtime_override=False: the NameError is the very fact the limitation is about
    assert entry_demotion(st, d, BY_ID["ANNOTATION-ONLY-READ"]) is None
    # an entry with runtime_override=True is still demoted by the same NameError (no dismissal swallows a crash)
    assert entry_demotion(st, d, BY_ID["REVEAL-ERROR-RECOVERY"]) is not None


HINT = "MYPY-UNBOUND-OPT-IN-CHECK"


def test_opt_in_hint_is_hint_only_and_narrow():
    e = BY_ID[HINT]
    assert not e.auto and e.verify is not None and e.title == "mypy opt-in check catches this; default-off"
    ok = Diagnostic(Tool.TY, 2, 1, Severity.ERROR, "unresolved-reference", "Name `x` used when not defined")
    st, d = name_case(ty=[ok])
    assert HINT in {x.id for x in matching_entries(st, d)}
    other = Diagnostic(Tool.TY, 2, 1, Severity.ERROR, "invalid-argument-type", "Argument is incorrect")
    st, d = name_case(ty=[other])
    assert HINT not in {x.id for x in matching_entries(st, d)}
    st, d = name_case(mypy=[Diagnostic(Tool.MYPY, 2, 1, Severity.ERROR, "name-defined", 'Name "x" is not defined')])
    assert HINT not in {x.id for x in matching_entries(st, d)}  # mypy reports it by default: no hint needed


COND_CLASS_BODY = (
    "from typing import Any\n\nx = None  # type: Any\n\n\nclass A:\n    if x:\n        def f(self, x: int) -> None:\n"
    "            pass\n        f(x, 1)\n    f(x, 1)\n"
)
FORWARD_BASE = "class A(B):\n    pass\n\n\nclass B:\n    pass\n"


@needs_tools
def test_opt_in_hint_appears_only_when_mypy_reports_the_name_with_the_opt_in_checks():
    # mypy --enable-error-code possibly-undefined reports `f` (default-off check): hint shown
    rep = pipeline().run_source(COND_CLASS_BODY, "optin-yes")
    shown = {i for i, hits in ((d.id, d.kb_hits) for d in rep.discrepancies) if HINT in hits}
    assert shown, [(d.id, d.kind.value, d.kb_hits) for d in rep.discrepancies]
    # a forward reference in a class base: mypy stays silent even with both checks on (true false negative): no hint
    rep = pipeline().run_source(FORWARD_BASE, "optin-no")
    assert rep.discrepancies and not any(HINT in d.kb_hits for d in rep.discrepancies)


@needs_tools
def test_opt_in_hint_never_closes_a_finding():
    rep = pipeline().run_source(COND_CLASS_BODY, "optin-never-closes")
    assert not any(f.decided_by == f"kb:{HINT}" or f.tier == Tier.DISMISSED for f in rep.findings
                   if f.discrepancy_id in {d.id for d in rep.discrepancies if HINT in d.kb_hits})


def test_repo_must_stay_live_programs_are_discovered():
    ids = {c["id"] for c in must_stay_live(ROOT / "calibration" / "must_stay_live")}
    assert {"live-ty_constant_fold_tuple_subclass", "live-mypy_stale_alias"} <= ids
