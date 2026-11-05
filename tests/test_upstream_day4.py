"""Day 4 morning: two entries added to known_upstream.json after the Day-3 verification (campaign/day3-verification.md).

* TY-4148 (crash)      astral-sh/ty#4148, ty stack overflow on ``__call__`` declared as an attribute of its own type.
* TY-876-ARGTYPE       astral-sh/ty#876 Flag item, the mypy-only [arg-type] row.

Reproducers live in tests/data/upstream_day4 (two Day-3 generated programs, the Day-3 Flag program, and two programs
that must stay live); every positive has controls."""
from __future__ import annotations

import json
from pathlib import Path

from typediff import kb
from typediff.crash_upstream import PATH, match_crash
from typediff.kb import entry_demotion, matching_entries
from typediff.models import Diagnostic, Discrepancy, DiscrepancyKind as K, RuntimeResult, Severity, Tool
from typediff.state import CaseState

DATA = Path(__file__).parent / "data" / "upstream_day4"
DATA3 = Path(__file__).parent / "data" / "upstream_day3"
TY_SO = "ty:signal-SIGABRT:stack-overflow"
RAW = json.loads(PATH.read_text())


def src(name: str, data: Path = DATA) -> str:
    return (data / f"{name}.py").read_text()


def crash_id(tool: str, sig: str, source: str) -> str | None:
    e = match_crash(source, tool, sig)
    return e["id"] if e else None


# ------------------------------------------------------------------------------------------------ TY-4148 (crash)
def test_ty4148_exact_issue_program():
    assert crash_id("ty", TY_SO, 'class C:\n    __call__: "C"\n\n\nC()()\n') == "TY-4148"
    assert crash_id("ty", TY_SO, 'class C:\n    __call__: "C"\n\n\ndef f(x: C) -> None:\n    x()\n') == "TY-4148"


def test_ty4148_day3_programs():
    assert crash_id("ty", TY_SO, src("ty4148_call_self_day3")) == "TY-4148"
    assert crash_id("ty", TY_SO, src("ty4148_self_union_day3")) == "TY-4148"


def test_ty4148_union_with_none_and_with_self():
    base = "from typing import Self\n\n\nclass C:\n    __call__: {ann}\n\n\nC()()\n"
    for ann in ('"C | None"', "Self", "Self | None"):
        assert crash_id("ty", TY_SO, base.format(ann=ann)) == "TY-4148", ann


def test_ty4148_is_ty_only_and_keeps_the_mypy_twin_separate():
    s = src("ty4148_call_self_day3")
    assert crash_id("mypy", "mypy:signal-SIGSEGV", s) == "MYPY-22361"  # mypy#22361 still closes the mypy crash
    assert crash_id("pyright", "pyright:internal:RangeError", s) is None


def test_ty4148_signature_gate():
    s = src("ty4148_call_self_day3")
    for sig in ("ty:signal-SIGABRT", "ty:timeout", "ty:signal-SIGKILL", "ty:exit2", "ty:panic@crates/x.rs:1:1"):
        assert crash_id("ty", sig, s) is None, sig


def test_ty4148_needs_the_call_and_the_self_typed_attribute():
    no_call = 'class C:\n    __call__: "C"\n\n\nx = C()\n'
    assert crash_id("ty", TY_SO, no_call) is None  # declaring the class is fine, the call is what crashes
    other = 'class C:\n    __call__: int\n\n\nC()()\n'
    assert crash_id("ty", TY_SO, other) is None  # not a cycle (ty reports call-non-callable)
    method = "class C:\n    def __call__(self) -> 'C':\n        return self\n\n\nC()()\n"
    assert crash_id("ty", TY_SO, method) is None  # a __call__ method is not the attribute form


def test_ty4148_does_not_swallow_other_stack_overflows():
    # a NEW ty bug (protocol flatten, d4v C2) with the same signature must stay live
    assert crash_id("ty", TY_SO, src("ty4148_control_protocol_flatten_new_bug")) is None
    # mutually recursive pair: same root cause, deliberately not matched (conservative)
    assert crash_id("ty", TY_SO, src("ty4148_control_mutual_pair")) is None
    # the older entries still win on their own programs
    assert crash_id("ty", TY_SO, src("ty_TB_protocol_stack_overflow", DATA3)) == "TY-4882"
    assert crash_id("ty", TY_SO, src("D7", DATA3)) == "TY-4900"
    assert crash_id("ty", TY_SO, src("C1", DATA3)) == "TY-4898"


def test_ty4148_entry_is_a_crash_entry_with_the_issue_url():
    e = next(x for x in RAW["entries"] if x["id"] == "TY-4148")
    assert e["kind"] == "crash" and e["tool"] == "ty" and e["url"] == "https://github.com/astral-sh/ty/issues/4148"
    assert "UPSTREAM-TY-4148" not in kb.BY_ID  # crash entries build no KB entry


# ------------------------------------------------------------------------------------------------ TY-876-ARGTYPE
ARG = [("arg-type", 'Argument 1 to "only_r" has incompatible type "F"; expected "Literal[F.R]"')]


def dg(tool, line, code, msg):
    return Diagnostic(tool, line, 1, Severity.ERROR, code, msg, None)


def disc(source: str, stmt: str, mypy=ARG, runtime: RuntimeResult | None = None):
    ln = next(i for i, x in enumerate(source.splitlines(), 1) if stmt in x)
    d = Discrepancy("D1", K.ONLY_MYPY, ln, ln, stmt, "", mypy=[dg(Tool.MYPY, ln, *m) for m in mypy], ty=[], pyright=[])
    st = CaseState("t", source, "3.13", {Tool.MYPY: d.mypy, Tool.TY: [], Tool.PYRIGHT: []},
                   runtime or RuntimeResult(status="success"), [], {}, {}, pyright_ran=True)
    return st, d


def ids(source: str, stmt: str, **kw) -> set[str]:
    st, d = disc(source, stmt, **kw)
    return {e.id for e in matching_entries(st, d)}


FLAG = ("import enum\nfrom typing import Literal\n\n\nclass F(enum.Flag):\n    R = 1\n    W = 2\n\n\n"
        "def only_r(x: Literal[F.R]) -> int:\n    return 1\n\n\ncombined = F.R | F.W\nonly_r(combined)\n")


def test_ty876_argtype_closes_the_day3_program():
    s = src("ty876_argtype_day3")
    assert "UPSTREAM-TY-876-ARGTYPE" in ids(s, "assert only_r(combined) == 1")


def test_ty876_argtype_closes_direct_combination_and_intflag():
    assert "UPSTREAM-TY-876-ARGTYPE" in ids(FLAG, "only_r(combined)")
    direct = FLAG.replace("only_r(combined)", "only_r(F.R | F.W)")
    assert "UPSTREAM-TY-876-ARGTYPE" in ids(direct, "only_r(F.R | F.W)")
    intflag = FLAG.replace("enum.Flag", "enum.IntFlag")
    assert "UPSTREAM-TY-876-ARGTYPE" in ids(intflag, "only_r(combined)")


def test_ty876_argtype_controls_stay_live():
    assert "UPSTREAM-TY-876-ARGTYPE" not in ids(FLAG.replace("enum.Flag", "enum.Enum"), "only_r(combined)")  # plain Enum
    no_combo = FLAG.replace("combined = F.R | F.W", "combined = F.W")
    assert "UPSTREAM-TY-876-ARGTYPE" not in ids(no_combo, "only_r(combined)")  # no Flag combination
    other = [("arg-type", 'Argument 1 to "only_r" has incompatible type "int"; expected "str"')]
    assert "UPSTREAM-TY-876-ARGTYPE" not in ids(FLAG, "only_r(combined)", mypy=other)  # another mypy message
    wrong_cls = [("arg-type", 'Argument 1 to "only_r" has incompatible type "G"; expected "Literal[G.R]"')]
    assert "UPSTREAM-TY-876-ARGTYPE" not in ids(FLAG, "only_r(combined)", mypy=wrong_cls)  # G is not a Flag of the program
    assignment = [("assignment", 'Incompatible types in assignment (expression has type "F", variable has type "Literal[F.R]")')]
    assert "UPSTREAM-TY-876-ARGTYPE" not in ids(FLAG, "only_r(combined)", mypy=assignment)  # other code


def test_ty876_argtype_steps_aside_when_cpython_raised_in_the_statement():
    s = FLAG
    ln = next(i for i, x in enumerate(s.splitlines(), 1) if "only_r(combined)" in x)
    ok_state, d = disc(s, "only_r(combined)")
    e = kb.BY_ID["UPSTREAM-TY-876-ARGTYPE"]
    assert entry_demotion(ok_state, d, e) is None  # CPython ran fine: the entry may close it
    rt = RuntimeResult(status="exception", exc_type="TypeError", exc_message="unsupported operand type(s) for +: 'int' and 'str'",
                       frames=[(ln, "only_r(combined)")])
    bad_state, d = disc(s, "only_r(combined)", runtime=rt)
    note = entry_demotion(bad_state, d, e)
    assert note is not None and "TypeError" in note.summary


def test_ty876_argtype_entry_schema():
    e = kb.BY_ID["UPSTREAM-TY-876-ARGTYPE"]
    assert e.runtime_override is False and e.demote is not None and e.example
    raw = next(x for x in RAW["entries"] if x["id"] == "TY-876-ARGTYPE")
    assert raw["url"] == "https://github.com/astral-sh/ty/issues/876" and raw["dismissal"] == "DUPLICATE"
