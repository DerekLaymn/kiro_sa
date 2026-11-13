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


STALE_ALIAS_PROGRAM = ROOT / "calibration" / "known_duplicates" / "mypy_stale_alias.py"


@needs_tools
def test_stale_alias_program_is_closed_by_exactly_the_ty_2792_entry():
    # Round 7 policy: this program (ty#2792, open) is a known duplicate. It was "must stay live" until Round 6. The
    # stale-alias guard of MYPY-13807-ALIASED-CONDITIONS still rejects it, so exactly UPSTREAM-TY-2792 closes it.
    rep = pipeline().run_source(STALE_ALIAS_PROGRAM.read_text(), "stale-alias")
    assert rep.findings
    assert [(f.tier, f.decided_by) for f in rep.findings] == [(Tier.DISMISSED, "kb:UPSTREAM-TY-2792")] * len(rep.findings), \
        [(f.decided_by, f.tier) for f in rep.findings]
    assert all(f.decided_by != f"kb:{AID}" for f in rep.findings)


@needs_tools
@pytest.mark.parametrize("name,old,new", [
    ("call of a method that assigns another attribute", "        self.x = None\n", "        self.y = None\n"),
    ("call that is not a method of the program", "    a.clear()\n", "    print(a)\n"),
    ("call before the aliased condition", "    is_none = a.x is None\n    a.clear()\n", "    a.clear()\n    is_none = a.x is None\n"),
])
def test_stale_alias_near_misses_are_not_closed_by_the_ty_2792_entries(name, old, new):
    # the same program without the trigger: what is still reported must not be closed by TY-2792 (the "before" variant
    # is legitimately closed by MYPY-13807, which is the entry that explains it)
    src = STALE_ALIAS_PROGRAM.read_text().replace(old, new)
    assert src != STALE_ALIAS_PROGRAM.read_text(), name
    rep = pipeline().run_source(src, "stale-alias-near-miss")
    assert not any(f.decided_by in ("kb:UPSTREAM-TY-2792", "kb:UPSTREAM-TY-2792-READONLY") for f in rep.findings), \
        (name, [(f.decided_by, f.tier) for f in rep.findings])


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


# ---------------------------------------------------------------- REVEAL-ERROR-RECOVERY through a flagged binding

RID = "REVEAL-ERROR-RECOVERY"
BIND_SRC = "a, b = 1\nprint(0)\nreveal_type(a)\n"  # the argument `a` starts at line 3, column 13


def bind_case(tool=Tool.TY, err_line=1, err_sev=Severity.ERROR, src=BIND_SRC, runtime=None, other_rev="int"):
    gradual, mine_rev, other_tool = ("Unknown", "Unknown", Tool.MYPY) if tool == Tool.TY else ("Any", "Any", Tool.TY)
    mine = Diagnostic(tool, 3, 13, Severity.NOTE, "revealed-type", "", revealed_type=mine_rev)
    other = Diagnostic(other_tool, 3, 13, Severity.NOTE, None, "", revealed_type=other_rev)
    err = Diagnostic(tool, err_line, 1, err_sev, "invalid-assignment", "m")
    diags = {tool: [err, mine], other_tool: [other], Tool.PYRIGHT: []}
    st = CaseState("t", src, "3.13", diags, runtime or RuntimeResult(status="success"), [], {}, {})
    ty, my = (mine, other) if tool == Tool.TY else (other, mine)
    return st, Discrepancy("D1", K.REVEAL_MISMATCH, 3, 3, "s", "", mypy=[my], ty=[ty], reveal_relation="gradual")


def rec_hit(st, d):
    return RID in {e.id for e in matching_entries(st, d)}


def test_recovery_through_a_flagged_binding_both_tools():
    assert rec_hit(*bind_case(Tool.TY))
    assert rec_hit(*bind_case(Tool.MYPY))
    # def / class / for / with bindings count through their own binding only
    assert rec_hit(*bind_case(src="def a() -> int:\n    return 1\nreveal_type(a)\n"))
    assert rec_hit(*bind_case(src="for a in 1:\n    pass\nreveal_type(a)\n"))
    assert rec_hit(*bind_case(src="with 1 as a:\n    pass\nreveal_type(a)\n"))


def test_recovery_through_a_binding_stays_narrow():
    assert not rec_hit(*bind_case(err_sev=Severity.WARNING))  # a warning is not an error
    assert not rec_hit(*bind_case(src="b = 1\nprint(0)\nreveal_type(a)\n"))  # the flagged statement binds another name
    assert not rec_hit(*bind_case(src="a, b = 1\nprint(0)\nreveal_type(len)\n"))  # argument reads no flagged name
    assert not rec_hit(*bind_case(err_line=3))  # error on the reveal statement itself is the other (inside-arg) branch
    assert not rec_hit(*bind_case(other_rev="Any"))  # both gradual
    assert not rec_hit(*bind_case(other_rev="list[Any]"))
    # an error inside a compound statement's body does not bind the names of its header or other statements
    assert not rec_hit(*bind_case(src="if 1:\n    print(0)\nreveal_type(a)\n", err_line=2))
    # the OTHER tool's earlier error does not explain this tool's gradual reveal
    st, d = bind_case(Tool.TY)
    st.diags[Tool.MYPY].append(st.diags[Tool.TY][0].__class__(Tool.MYPY, 1, 1, Severity.ERROR, "assignment", "m"))
    st.diags[Tool.TY] = [x for x in st.diags[Tool.TY] if x.revealed_type is not None]
    assert not rec_hit(st, d)


def test_recovery_through_a_binding_keeps_a_cpython_exception_in_review():
    rt = RuntimeResult(status="exception", exc_type="ValueError", exc_message="x", exc_line=3, frames=[(3, "<module>")])
    assert not rec_hit(*bind_case(runtime=rt))
    rt = RuntimeResult(status="exception", exc_type="ValueError", exc_message="x", exc_line=1, frames=[(1, "<module>")])
    assert rec_hit(*bind_case(runtime=rt))  # raised at the (flagged) binding, not at the reveal


@needs_tools
def test_recovery_through_a_binding_real_tools_keeps_the_error_visible():
    src = 'a, b, *c, d = "a"\nreveal_type(a)\n'
    rep = pipeline().run_source(src, "bind-recovery")
    by = {f.discrepancy_id: f for f in rep.findings}
    kinds = {d.id: d.kind for d in rep.discrepancies}
    reveals = [i for i, k in kinds.items() if k == K.REVEAL_MISMATCH]
    assert reveals, [(d.id, d.kind.value) for d in rep.discrepancies]
    # the reveal row (ty Unknown after its own unpacking error) is closed; the error itself is NOT swallowed
    assert any(by[i].decided_by == f"kb:{RID}" and by[i].tier == Tier.DISMISSED for i in reveals)
    others = [f for i, f in by.items() if i not in reveals]
    assert others and not any(f.decided_by == f"kb:{RID}" for f in others)


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


def test_known_duplicate_programs_moved_out_of_must_stay_live():
    # Round 7 decision: the two programs are known duplicates of open ty issues, closed by named entries (tests above and in
    # test_stage3_round2.py). must_stay_live keeps its loader and classification (tests above) but holds no program now.
    assert must_stay_live(ROOT / "calibration" / "must_stay_live") == []
    names = {p.name for p in (ROOT / "calibration" / "known_duplicates").glob("*.py")}
    assert names == {"ty_constant_fold_tuple_subclass.py", "mypy_stale_alias.py"}
