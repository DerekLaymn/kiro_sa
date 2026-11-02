"""Origin oracle: expectation comments of the harvested suite vs each tool's reveal (kb-loop round 1)."""

from __future__ import annotations

from typediff.kb import BY_ID, entry_demotion, matching_entries
from typediff.models import Diagnostic, Discrepancy, DiscrepancyKind as K, RuntimeProbe, RuntimeResult, Severity, Tool
from typediff.origin import expectations
from typediff.state import CaseState


def rv(tool, line, text):
    return Diagnostic(tool, line, 1, Severity.NOTE, "revealed-type", "Revealed type", revealed_type=text)


def case(src, mypy_rev, ty_rev, relation, runtime=None, line=1, header=True):
    if header:
        src, line = ("# origin: ruff mdtest x.md block 0\n" if "# revealed:" in src else "# origin: python/mypy c.test [case t]\n") + src, line + 1
    m, t = rv(Tool.MYPY, line, mypy_rev), rv(Tool.TY, line, ty_rev)
    st = CaseState("t", src, "3.13", {Tool.MYPY: [m], Tool.TY: [t], Tool.PYRIGHT: []},
                   runtime or RuntimeResult(status="success"), [], {}, {})
    d = Discrepancy("D1", K.REVEAL_MISMATCH, line, line, "s", "", mypy=[m], ty=[t], reveal_relation=relation)
    return st, d


def ids(st, d):
    return {e.id for e in matching_entries(st, d)}


TY_SRC = "reveal_type(f())  # revealed: tuple[Unknown, ...]\n"
MYPY_SRC = 'reveal_type(f())  # N: Revealed type is "builtins.int"\n'


def test_expectation_parsing():
    assert expectations(TY_SRC)[1] == ("ty", ("tuple[Unknown, ...]",))
    assert expectations(MYPY_SRC)[1] == ("mypy", ("builtins.int",))
    assert expectations("x = 1  # a comment\n") == {}


def test_ty_origin_matches_mypy_is_less_precise_dismisses():
    st, d = case(TY_SRC, "Any", "tuple[Unknown, ...]", "gradual")
    assert "ORIGIN-ORACLE-REVEAL" in ids(st, d)


def test_mypy_origin_matches_ty_unknown_dismisses():
    st, d = case(MYPY_SRC, "int", "Unknown", "gradual")
    assert "ORIGIN-ORACLE-REVEAL" in ids(st, d)


def test_oracle_reveal_is_hint_only_and_never_dismisses():
    assert BY_ID["ORIGIN-ORACLE-REVEAL"].auto is False


def test_precision_relation_when_origin_is_the_precise_one_stays_in_review():
    # circular: ty's more precise answer would be excused by ty's own suite
    st, d = case("reveal_type(f())  # revealed: Literal[1]\n", "int", "Literal[1]", "ty_more_precise")
    assert "ORIGIN-ORACLE-REVEAL" not in ids(st, d)
    assert "ORIGIN-ORACLE-NOTE" in ids(st, d)


def test_header_must_be_at_the_top_of_the_file():
    src = "x = 1\n" * 10 + "# origin: ruff mdtest x.md block 0\nreveal_type(f())  # revealed: tuple[Unknown, ...]\n"
    st, d = case(src, "Any", "tuple[Unknown, ...]", "gradual", line=12, header=False)
    assert not ({"ORIGIN-ORACLE-REVEAL", "ORIGIN-ORACLE-NOTE", "ORIGIN-MISMATCH"} & ids(st, d))


# ---------------------------------------------------------------- negatives (near misses that must NOT be dismissed)


def test_other_tool_more_precise_is_not_dismissed():
    # ty's blessed answer is the gradual one; mypy is MORE precise -> mypy's answer might expose a ty gap
    st, d = case("reveal_type(f())  # revealed: Unknown | Literal[1]\n", "Literal[1]", "Unknown | Literal[1]", "gradual")
    assert "ORIGIN-ORACLE-REVEAL" not in ids(st, d)


def test_different_types_not_dismissed():
    st, d = case("reveal_type(f())  # revealed: str\n", "int", "str", "different")
    assert "ORIGIN-ORACLE-REVEAL" not in ids(st, d)
    assert "ORIGIN-ORACLE-NOTE" in ids(st, d)  # explained, not dismissed


def test_origin_not_matching_its_own_expectation_is_flagged_not_dismissed():
    st, d = case("reveal_type(f())  # revealed: str\n", "Any", "None | Unknown", "gradual")
    got = ids(st, d)
    assert "ORIGIN-MISMATCH" in got and "ORIGIN-ORACLE-REVEAL" not in got
    assert BY_ID["ORIGIN-MISMATCH"].auto is False


def test_precision_when_origin_is_the_coarse_one_not_dismissed():
    st, d = case("reveal_type(f())  # revealed: int\n", "Literal[1]", "int", "mypy_more_precise")
    assert "ORIGIN-ORACLE-REVEAL" not in ids(st, d)


def test_no_expectation_comment_not_matched():
    st, d = case("reveal_type(f())\n", "Any", "tuple[Unknown, ...]", "gradual")
    assert not ({"ORIGIN-ORACLE-REVEAL", "ORIGIN-ORACLE-NOTE", "ORIGIN-MISMATCH"} & ids(st, d))


def test_cpython_contradiction_demotes_the_dismissal():
    probe = RuntimeProbe(2, {"type": "builtins.str", "mro": ["builtins.str", "builtins.object"], "repr": "'x'"})
    rt = RuntimeResult(status="success", probes=[probe], executed_lines=[2])
    st, d = case("reveal_type(f())  # revealed: int\n", "Unknown", "int", "gradual", runtime=rt)
    # origin ty matches `int`, mypy Unknown is less precise -> matches, but the runtime value (a str) is outside ty's int
    assert "ORIGIN-ORACLE-REVEAL" in ids(st, d)
    assert entry_demotion(st, d, BY_ID["ORIGIN-ORACLE-REVEAL"]) is not None


def test_spec_defined_narrowing_is_not_dismissed():
    src = "def f(x: object):\n    if isinstance(x, int):\n        reveal_type(x)  # revealed: int\n"
    st, d = case(src, "Any", "int", "gradual", line=3)
    assert "ORIGIN-ORACLE-REVEAL" not in ids(st, d)
    src_plain = "def f(x: object):\n    if True:\n        reveal_type(x)  # revealed: int\n"
    st, d = case(src_plain, "Any", "int", "gradual", line=3)
    assert "ORIGIN-ORACLE-REVEAL" in ids(st, d)


def test_bug_report_comment_without_suite_header_is_not_an_expectation():
    # calibration: ty#4841's `# revealed: None` is the reporter's observation of ty's (wrong) output
    st, d = case("reveal_type(f())  # revealed: tuple[Unknown, ...]\n", "Any", "tuple[Unknown, ...]", "gradual", header=False)
    assert not ({"ORIGIN-ORACLE-REVEAL", "ORIGIN-ORACLE-NOTE", "ORIGIN-MISMATCH"} & ids(st, d))
