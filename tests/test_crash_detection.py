"""kb-loop round 2: crash-detection defects found by the crash25 check (P1 signal exits and pyright internal errors,
P2 pyright timeout double count, P3 excerpt head+tail, P4 finer signatures, P5 rerun-before-reporting flag)."""

from __future__ import annotations

from typediff.models import Tier, Tool, Verdict
from typediff.parsers import head_tail, parse_mypy, parse_pyright, parse_ty
from typediff.rules import crash_findings

PYRIGHT_STDERR = ("An internal error occurred while type checking file \"/tmp/x/case.py\": RangeError: Maximum call stack size "
                  "exceeded\n" + "\n".join(f"    at frame{i} (typeEvaluator.ts:{i}:1)" for i in range(60)))


# P1 ---------------------------------------------------------------------------------------------------------------

def test_mypy_signal_death_is_a_confirmed_crash():
    _, crashes = parse_mypy("", "", -11, "case.py")
    assert [(c.kind, c.signature) for c in crashes] == [("signal", "mypy:signal-SIGSEGV")]
    f = crash_findings(crashes)[0]
    assert f.verdict == Verdict.BUG and f.tier == Tier.CONFIRMED and f.decided_by == "rule:crash:signal"


def test_ty_stack_overflow_signature():
    _, crashes = parse_ty("", "thread '<unknown>' (1) has overflowed its stack\nfatal runtime error: stack overflow, aborting", -6, "case.py")
    assert crashes[0].kind == "signal" and crashes[0].signature == "ty:signal-SIGABRT:stack-overflow"


def test_pyright_internal_error_without_json():
    _, crashes = parse_pyright("", PYRIGHT_STDERR, 2, "case.py")
    assert [(c.kind, c.signature) for c in crashes] == [("internal_error", "pyright:internal:RangeError")]
    assert crash_findings(crashes)[0].tier == Tier.CONFIRMED


def test_usage_error_exit_is_still_needs_human():  # negatives: a positive exit code without a crash banner is not a crash
    _, crashes = parse_mypy("", "usage: mypy ...", 2, "case.py")
    assert crashes[0].kind == "abnormal_exit"
    f = crash_findings(crashes)[0]
    assert f.verdict == Verdict.NEEDS_HUMAN and f.tier == Tier.REVIEW
    _, crashes = parse_pyright("", "error: unknown option --foo", 2, "case.py")
    assert crashes[0].kind == "abnormal_exit"


def test_normal_runs_are_not_crashes():
    assert parse_mypy("case.py:1:1: error: boom [misc]", "", 1, "case.py")[1] == []
    assert parse_ty("", "", 0, "case.py")[1] == []


# P2 ---------------------------------------------------------------------------------------------------------------

def test_pyright_timeout_is_not_double_counted():
    _, crashes = parse_pyright("", "TIMEOUT after 120s", None, "case.py")
    assert crashes == []  # Runners.check adds the single `timeout` crash for exit_code None


# P3 ---------------------------------------------------------------------------------------------------------------

def test_excerpt_keeps_head_and_tail():
    _, crashes = parse_pyright("", PYRIGHT_STDERR, 2, "case.py")
    ex = crashes[0].excerpt
    assert ex.splitlines()[0].startswith("An internal error occurred")
    assert "RangeError: Maximum call stack size exceeded" in ex and "frame59" in ex and "omitted" in ex


def test_short_output_is_kept_whole():
    assert head_tail("a\nb\nc") == "a\nb\nc"


# P4 ---------------------------------------------------------------------------------------------------------------

def test_signatures_distinguish_signal_kinds():
    sigs = {parse_mypy("", "", c, "case.py")[1][0].signature for c in (-11, -6, -9)}
    assert sigs == {"mypy:signal-SIGSEGV", "mypy:signal-SIGABRT", "mypy:signal-SIGKILL"}


# P5 ---------------------------------------------------------------------------------------------------------------

def test_crash_candidates_carry_the_rerun_before_reporting_note():
    _, crashes = parse_ty("", "thread 'x' has overflowed its stack", -6, "case.py")
    notes = crash_findings(crashes)[0].review_notes
    assert any(n.startswith("RERUN-BEFORE-REPORTING") and "newest released ty" in n for n in notes)
