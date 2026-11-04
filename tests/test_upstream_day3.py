"""Day 3: team-filed upstream issues recorded in known_upstream.json (crash entries, discrepancy entries, priors).

Reproducers are real programs under tests/data/upstream_day3 (copied from the crash25 repros, the xfer/var probes and
the 2026-10-27 LLM run); each positive has controls that must stay live."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from typediff import kb
from typediff.crash_upstream import _CRASH_REQUIRES, PATH, load, match_crash
from typediff.models import Crash, Dismissal, Tier, Tool, Verdict
from typediff.rules import crash_findings

DATA = Path(__file__).parent / "data" / "upstream_day3"
TY_SO = "ty:signal-SIGABRT:stack-overflow"
MYPY_SEGV = "mypy:signal-SIGSEGV"


def src(name: str) -> str:
    return (DATA / f"{name}.py").read_text()


def crashes_as(tool: str, sig: str, name: str) -> str | None:
    e = match_crash(src(name), tool, sig)
    return e["id"] if e else None


# ------------------------------------------------------------------------------------------------ crash positives
@pytest.mark.parametrize("name,tool,sig,want", [
    ("ty_TB_protocol_stack_overflow", "ty", TY_SO, "TY-4882"),
    ("t20a", "ty", TY_SO, "TY-4882"),
    ("ty_20", "ty", TY_SO, "TY-4882"),
    ("ty_TA_nested_tuple_compare", "ty", "ty:timeout", "TY-4883"),
    ("ty_TA_depth24", "ty", "ty:timeout", "TY-4883"),
    ("C1", "ty", TY_SO, "TY-4898"),
    ("C3", "ty", TY_SO, "TY-4898"),
    ("E1", "ty", "ty:signal-SIGABRT", "TY-4899"),
    ("E2", "ty", "ty:signal-SIGABRT", "TY-4899"),
    ("E6", "ty", "ty:signal-SIGABRT", "TY-4899"),
    ("E8", "ty", "ty:panic@crates/ty_python_semantic/src/x.rs:1:1", "TY-4899"),
    ("E10", "ty", "ty:signal-SIGABRT", "TY-4899"),
    ("D1", "ty", TY_SO, "TY-4900"),
    ("D7", "ty", TY_SO, "TY-4900"),
    ("D10", "ty", TY_SO, "TY-4900"),
    ("D11", "ty", TY_SO, "TY-4900"),
    ("mypy_A_typealias_segfault", "mypy", MYPY_SEGV, "MYPY-22343"),
    ("mypy_A_typealias_segfault", "mypy", "mypy:RecursionError@mypy/types.py:get_proper_type", "MYPY-22343"),
    ("mypy_E_typevar_default_self", "mypy", MYPY_SEGV, "MYPY-22344"),
    ("mypy_25", "mypy", MYPY_SEGV, "MYPY-22344"),
    ("B1", "mypy", MYPY_SEGV, "MYPY-22360"),
    ("B4", "mypy", MYPY_SEGV, "MYPY-22360"),
    ("D1", "mypy", MYPY_SEGV, "MYPY-22360"),
    ("D7", "mypy", MYPY_SEGV, "MYPY-22360"),
    ("D9", "mypy", MYPY_SEGV, "MYPY-22360"),
    ("D10", "mypy", MYPY_SEGV, "MYPY-22360"),
    ("A1", "mypy", MYPY_SEGV, "MYPY-22361"),
    ("A2", "mypy", MYPY_SEGV, "MYPY-22361"),
    ("A4", "mypy", MYPY_SEGV, "MYPY-22361"),
    ("A5", "mypy", MYPY_SEGV, "MYPY-22361"),
    ("A6", "mypy", MYPY_SEGV, "MYPY-22361"),
    ("pyright_init_attr", "pyright", "pyright:internal:RangeError", "PYRIGHT-11961"),
    ("pyright_new_attr", "pyright", "pyright:internal:RangeError", "PYRIGHT-11961"),
    ("pyright_call_metaclass", "pyright", "pyright:internal:RangeError", "PYRIGHT-11961"),
])
def test_crash_reproducer_closes_with_its_id(name, tool, sig, want):
    assert crashes_as(tool, sig, name) == want


def test_pyright_hang_closes_with_its_id():
    s = "type GrowingList[T] = list[GrowingList[T | GrowingList[T]]]\ndef f(x: GrowingList[int]): pass\n"
    assert match_crash(s, "pyright", "pyright:timeout")["id"] == "PYRIGHT-11960"
    assert match_crash("type GrowingList[T] = list[GrowingList[T | GrowingList[T]]]\n", "pyright", "pyright:timeout") is None


# ------------------------------------------------------------------------------------------------ crash controls
@pytest.mark.parametrize("name", ["C4", "C5", "C6", "E3", "E4", "E5", "E7", "E9", "A3", "A8", "A9", "A10", "B3", "B5",
                                  "B6", "D4", "D8", "mypy_B_typealias_hang"])
@pytest.mark.parametrize("tool,sig", [("ty", TY_SO), ("ty", "ty:signal-SIGABRT"), ("ty", "ty:timeout"),
                                     ("mypy", MYPY_SEGV), ("pyright", "pyright:internal:RangeError")])
def test_controls_never_match_even_with_a_matching_signature(name, tool, sig):
    assert crashes_as(tool, sig, name) is None


def test_unfiled_ty_overflow_on_A1_matches_nothing():
    assert crashes_as("ty", TY_SO, "A1") is None
    assert crashes_as("mypy", MYPY_SEGV, "A1") == "MYPY-22361"  # but mypy's crash on the same program is #22361


def test_mypy_hang_variant_is_not_22343():
    assert crashes_as("mypy", MYPY_SEGV, "mypy_B_typealias_hang") is None
    assert crashes_as("mypy", "mypy:timeout", "mypy_A_typealias_segfault") is None


def test_the_other_decorated_get_crash_stays_live():
    assert crashes_as("mypy", MYPY_SEGV, "A7") is None


def test_same_program_two_tools_two_issues():
    assert crashes_as("ty", TY_SO, "D7") == "TY-4900"
    assert crashes_as("mypy", MYPY_SEGV, "D7") == "MYPY-22360"
    assert crashes_as("pyright", "pyright:internal:RangeError", "D7") is None


def test_signature_gate():
    assert crashes_as("ty", "ty:timeout", "ty_TB_protocol_stack_overflow") is None
    assert crashes_as("ty", "ty:exit2", "ty_TB_protocol_stack_overflow") is None
    assert crashes_as("mypy", "mypy:exit2", "A2") is None
    assert crashes_as("ty", "ty:signal-SIGABRT", "C1") is None  # memory abort is not the #4898 stack overflow


def test_broken_source_is_no_match():
    assert match_crash("def (:\n", "ty", TY_SO) is None


# ------------------------------------------------------------------------------------------------ pipeline level
def _judge(source: str, crash: Crash):
    from typediff.pipeline import Pipeline
    from typediff.llm import CachedLLM, NullLLM
    from typediff.models import RuntimeResult
    from typediff.state import CaseState

    pipe = Pipeline(llm=CachedLLM(NullLLM()))
    st = CaseState("t", source, "3.13", {}, RuntimeResult(status="success"), [crash], {}, {})
    return pipe._judge(st)


def test_pipeline_dismisses_matching_crash_with_url_in_note():
    rep = _judge(src("D7"), Crash(Tool.TY, "signal", TY_SO, "", -6))
    f = rep.findings[0]
    assert f.tier == Tier.DISMISSED and f.dismissal == Dismissal.DUPLICATE
    assert any("https://github.com/astral-sh/ty/issues/4900" in n and "TY-4900" in n for n in f.review_notes)
    rep = _judge(src("D7"), Crash(Tool.MYPY, "signal", MYPY_SEGV, "", -11))
    f = rep.findings[0]
    assert f.tier == Tier.DISMISSED and any("https://github.com/python/mypy/issues/22360" in n for n in f.review_notes)


def test_pipeline_unmatched_crash_stays_confirmed():
    rep = _judge(src("A1"), Crash(Tool.TY, "signal", TY_SO, "", -6))
    f = rep.findings[0]
    assert f.verdict == Verdict.BUG and f.tier == Tier.CONFIRMED and f.dismissal is None
    rep = _judge("x = 1\n", Crash(Tool.TY, "signal", TY_SO, "", -6))
    assert rep.findings[0].tier == Tier.CONFIRMED


def test_pipeline_abnormal_exit_is_never_dismissed():
    rep = _judge(src("D7"), Crash(Tool.TY, "abnormal_exit", TY_SO, "", 2))
    f = rep.findings[0]
    assert f.verdict == Verdict.NEEDS_HUMAN and f.tier == Tier.REVIEW and f.dismissal is None


def test_crash_findings_without_extension_input_unchanged():
    f = crash_findings([Crash(Tool.TY, "signal", TY_SO, "", -6)])[0]
    assert f.tier == Tier.CONFIRMED and f.symptom is not None


def test_crash_entries_are_not_kb_entries():
    assert "UPSTREAM-TY-4882" not in kb.BY_ID
    assert not [e for e in kb.ENTRIES if e.id.startswith("UPSTREAM-") and "4882" in e.id]


# ------------------------------------------------------------------------------------------------ data integrity
RAW = json.loads(PATH.read_text())
ALLOWED_KINDS = {"only_mypy", "only_ty", "reveal_mismatch", "concern_mismatch", "crash"}


def test_ids_unique_and_urls_github():
    ids = [e["id"] for e in RAW["entries"]] + [p["id"] for p in RAW["prior_stances"]]
    assert len(ids) == len(set(ids)), [i for i in ids if ids.count(i) > 1]
    for e in RAW["entries"] + RAW["prior_stances"]:
        assert e["url"].startswith("https://github.com/")


def test_entry_schema():
    for e in RAW["entries"]:
        assert e["kind"] in ALLOWED_KINDS
        assert e["dismissal"] in {d.value for d in Dismissal}
        if e["kind"] == "crash":
            assert e["tool"] in {"mypy", "ty", "pyright"}
            re.compile(e["signature"])
            assert e["requires"] in _CRASH_REQUIRES
        elif e.get("requires"):
            assert e["requires"] in kb._REQUIRES


def test_every_crash_requires_function_is_used_and_loaded():
    used = {e["requires"] for e in load()}
    assert used == set(_CRASH_REQUIRES)
