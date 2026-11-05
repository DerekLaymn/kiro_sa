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
    ("E6", "ty", "ty:signal-SIGKILL", "TY-4899"),
    ("E6", "ty", "ty:timeout", "TY-4899"),
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


def test_ty_overflow_on_A1_is_ty4148_and_mypy_crash_is_22361():
    # Day 3 left the ty crash on A1 unfiled and live; Day 4 added TY-4148 (astral-sh/ty#4148, the same two-line program)
    assert crashes_as("ty", TY_SO, "A1") == "TY-4148"
    assert crashes_as("mypy", MYPY_SEGV, "A1") == "MYPY-22361"  # mypy's crash on the same program is #22361


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
    # SIGKILL belongs to TY-4899 only (E6 memory blow-up); no other ty entry accepts it
    for name in ("ty_TB_protocol_stack_overflow", "C1", "D1", "ty_TA_depth24"):
        assert crashes_as("ty", "ty:signal-SIGKILL", name) is None
    assert crashes_as("ty", "ty:signal-SIGKILL", "E3") is None  # control for the TY-4899 shape
    # bare pyright:internal (not the RangeError) is not PYRIGHT-11961
    assert crashes_as("pyright", "pyright:internal", "pyright_init_attr") is None


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
    # a ty stack overflow no entry covers (protocol flatten, not filed upstream as of Day 4)
    unfiled = (DATA.parent / "upstream_day4" / "ty4148_control_protocol_flatten_new_bug.py").read_text()
    rep = _judge(unfiled, Crash(Tool.TY, "signal", TY_SO, "", -6))
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


# ------------------------------------------------------------------------------------------------ discrepancy entries
from typediff.kb import matching_entries  # noqa: E402
from typediff.models import Diagnostic, Discrepancy, DiscrepancyKind as K, RuntimeResult, Severity  # noqa: E402
from typediff.priors import find_priors  # noqa: E402
from typediff.state import CaseState  # noqa: E402


def line_of(source: str, stmt: str, after: str | None = None) -> int:
    lines = source.splitlines()
    start = next(i for i, ln in enumerate(lines) if after in ln) if after else 0
    return next(i for i in range(start, len(lines)) if stmt in lines[i] and not lines[i].lstrip().startswith("#")) + 1


def dg(tool, line, code, msg, rev=None):
    return Diagnostic(tool, line, 1, Severity.ERROR, code, msg, rev)


def disc(source, stmt, kind, ty=(), mypy=(), pyright=(), after=None):
    """CaseState + Discrepancy shaped like the real pipeline output for `stmt` (diagnostics: (code, message))."""
    ln = line_of(source, stmt, after)
    d = Discrepancy("D1", kind, ln, ln, source.splitlines()[ln - 1].strip(), "",
                    mypy=[dg(Tool.MYPY, ln, *i) for i in mypy], ty=[dg(Tool.TY, ln, *i) for i in ty],
                    pyright=[dg(Tool.PYRIGHT, ln, *i) for i in pyright])
    st = CaseState("t", source, "3.13", {Tool.MYPY: d.mypy, Tool.TY: d.ty, Tool.PYRIGHT: d.pyright},
                   RuntimeResult(status="success"), [], {}, {}, pyright_ran=True)
    return st, d


def ids(st, d):
    return {e.id for e in matching_entries(st, d)}


def closes(src_text, stmt, kind, want, **kw):
    return f"UPSTREAM-{want}" in ids(*disc(src_text, stmt, kind, **kw))


def no_upstream(src_text, stmt, kind, **kw):
    return not {i for i in ids(*disc(src_text, stmt, kind, **kw)) if i.startswith("UPSTREAM-")}


REV_UNKNOWN = [(None, "Revealed type: `Unknown`")]
ASSERT_UNKNOWN = [("type-assertion-failure", "Type `Unknown` does not match asserted type `int`")]
ASSIGN = [("assignment", 'Incompatible types in assignment (expression has type "int", variable has type "str")')]


def test_ty4884_generic_typeddict_solver():
    w = src("bug-05-ty-generic-typeddict-crash-witness")
    assert closes(w, "y: str = first(a)", K.ONLY_MYPY, "TY-4884", mypy=ASSIGN, pyright=[("reportAssignmentType", "x")])
    b = src("bug-05-typeddict-ty-generic-typeddict-typevar-unknown")
    assert closes(b, "x: int = first(c)", K.ONLY_MYPY, "TY-4884", mypy=ASSIGN)
    assert closes(b, "reveal_type(first(a))", K.REVEAL_MISMATCH, "TY-4884-REVEAL",
                  mypy=[(None, 'Revealed type is "int"')], ty=REV_UNKNOWN)
    p = src("probe-bug05-typeddict-variants")
    assert closes(p, "assert_type(first_old(a), int)", K.ONLY_TY, "TY-4884-ASSERT", ty=ASSERT_UNKNOWN)
    assert closes(p, "assert_type(first_new(b), int)", K.ONLY_TY, "TY-4884-ASSERT", ty=ASSERT_UNKNOWN)


def test_ty4884_controls():
    p = src("probe-bug05-typeddict-variants")
    assert no_upstream(p, "assert_type(unbox(c), int)", K.ONLY_TY, ty=ASSERT_UNKNOWN)  # ordinary generic class
    assert no_upstream(p, "assert_type(gerbil(", K.ONLY_TY, ty=ASSERT_UNKNOWN)  # nested TypedDict is ty#4803, not #4884
    r = src("probe-bug02-bug05-runtime-and-assignability")
    assert no_upstream(r, "takes_int(c)", K.ONLY_MYPY, mypy=ASSIGN)  # no TypeVar solved
    assert no_upstream(r, "z: Resp[int] = c", K.ONLY_MYPY, mypy=ASSIGN)  # no call
    w = src("bug-05-ty-generic-typeddict-crash-witness")
    assert no_upstream(w, "print(y.upper())", K.ONLY_MYPY, mypy=ASSIGN)  # no call to the solving function


CB_ARG = [("invalid-argument-type", "Argument to function `use` is incorrect: Expected `Handler[int]`, found `Handler[float]`")]


def cb_assign(cls, a, b):
    return [("invalid-assignment", f"Object of type `{cls}[{a}]` is not assignable to `{cls}[{b}]`")]


def test_mypy22339_callable_attribute_variance():
    b = src("bug-03-generics-mypy-callable-attr-contravariant")
    assert closes(b, "use(hf)", K.ONLY_TY, "MYPY-22339", ty=CB_ARG)
    p = src("probe-bug03-variance-variants")
    assert closes(p, "cic: CbInit[bool] = ci", K.ONLY_TY, "MYPY-22339", ty=cb_assign("CbInit", "int", "bool"))
    assert closes(p, "caf: CbAnn[bool] = ca", K.ONLY_TY, "MYPY-22339", ty=cb_assign("CbAnn", "int", "bool"))


def test_mypy22339_controls_stay_live():
    p = src("probe-bug03-variance-variants")
    for stmt, cls, a, b in [("cff: CbFinal[bool] = cf", "CbFinal", "int", "bool"),
                            ("cmf: CbMethod[bool] = cm", "CbMethod", "int", "bool"),
                            ("pf: Plain[float] = p", "Plain", "int", "float"),
                            ("prf: Producer[object] = pr", "Producer", "float", "object")]:
        assert no_upstream(p, stmt, K.ONLY_TY, ty=cb_assign(cls, a, b)), stmt


STALE_OP = [("unsupported-operator", "Operator `+` is not supported between objects of type `None` and `Literal[1]`")]
REV = dict(mypy=[(None, 'Revealed type is "int"')], ty=[(None, "Revealed type: `None`")])


def test_mypy20969_stale_index_narrowing():
    b = src("bug-01-narrowing-mypy-stale-index-narrowing")
    assert closes(b, "return xs[0] + 1", K.ONLY_TY, "MYPY-20969", ty=STALE_OP)
    assert closes(b, "reveal_type(xs[0])", K.REVEAL_MISMATCH, "MYPY-20969-REVEAL", **REV)
    p = src("probe-bug01-index-variants")
    assert closes(p, "reveal_type(xs[0])", K.REVEAL_MISMATCH, "MYPY-20969-REVEAL", after="def list_idx", **REV)
    assert closes(p, 'reveal_type(d["k"])', K.REVEAL_MISMATCH, "MYPY-20969-REVEAL", **REV)
    assert closes(p, "reveal_type(t[0])", K.REVEAL_MISMATCH, "MYPY-20969-REVEAL", **REV)


def test_mypy20969_controls_stay_live():
    p = src("probe-bug01-index-variants")
    assert no_upstream(p, "reveal_type(b.v)", K.REVEAL_MISMATCH, **REV)  # attribute: mypy resets
    assert no_upstream(p, "reveal_type(xs[i])", K.REVEAL_MISMATCH, **REV)  # non-literal index
    assert no_upstream(p, "reveal_type(xs[0])", K.REVEAL_MISMATCH, after="def del_form", **REV)  # del, not assignment
    # narrowed but never assigned: not this bug
    s = "def a(xs: list[int | None]) -> int:\n    if xs[0] is not None:\n        return xs[0] + 'x'\n    return 0\n"
    assert no_upstream(s, "return xs[0]", K.ONLY_TY, ty=STALE_OP)
    # assigned in a different function than the use
    s = ("def a(xs: list[int | None]) -> None:\n    if xs[0] is not None:\n        xs[0] = None\n\n\n"
         "def b(xs: list[int | None]) -> int:\n    return xs[0] + 1\n")
    assert no_upstream(s, "return xs[0] + 1", K.ONLY_TY, ty=STALE_OP)


def test_mypy21937_flag_is_chain():
    b = src("bug-06-enums-mypy-flag-is-narrowing-else-unreachable")
    bad = [("unsupported-operator", 'Operator `+` is not supported between objects of type `Literal[1]` and `Literal["bad"]`')]
    assert closes(b, 'return 1 + "bad"', K.ONLY_TY, "MYPY-21937", ty=bad)
    assert no_upstream(b.replace("enum.Flag", "enum.Enum"), 'return 1 + "bad"', K.ONLY_TY, ty=bad)  # plain Enum: mypy is right
    assert no_upstream(b, 'return "R"', K.ONLY_TY, ty=bad)  # inside the chain, not in the final else
    p = src("probe-bug06-flag-param-and-local")
    assert closes(p, 'return 1 + "bad"', K.ONLY_TY, "MYPY-21937", ty=bad)
    two = ("import enum\n\n\nclass F(enum.Flag):\n    R = 1\n    W = 2\n\n\ndef h(x: F) -> str:\n    if x is F.R:\n"
           "        return 'R'\n    else:\n        return 1 + 'bad'\n")
    assert no_upstream(two, "return 1 + 'bad'", K.ONLY_TY, ty=bad)  # a single test is not a chain


def test_ty876_flag_expansion():
    b = src("bug-02-enums-ty-flag-or-literal-union")
    rev = dict(mypy=[(None, 'Revealed type is "case.F"')], ty=[(None, "Revealed type: `Literal[F.R, F.W]`")])
    assert closes(b, "reveal_type(a)", K.REVEAL_MISMATCH, "TY-876", **rev)
    assert no_upstream(b.replace("enum.Flag", "enum.Enum"), "reveal_type(a)", K.REVEAL_MISMATCH, **rev)
    o = src("probe-bug02-flag-operators")
    assert closes(o, "reveal_type(F.R | F.W)", K.REVEAL_MISMATCH, "TY-876", **rev)
    assert closes(o, "reveal_type(I.R | I.W)", K.REVEAL_MISMATCH, "TY-876",
                  mypy=[(None, 'Revealed type is "case.I"')], ty=[(None, "Revealed type: `Literal[I.R]`")])
    a = src("bug-02-ty-flag-or-assert-type")
    fail = [("type-assertion-failure", "Type `Literal[F.R, F.W]` does not match asserted type `F`")]
    assert closes(a, "assert_type(v, F)", K.ONLY_TY, "TY-876-ASSERT", ty=fail)
    assert no_upstream(a.replace("enum.Flag", "enum.Enum"), "assert_type(v, F)", K.ONLY_TY, ty=fail)
    plain = "import enum\n\n\nclass E(enum.Enum):\n    A = 1\n\n\nx = E.A\nreveal_type(x)\n"
    assert no_upstream(plain, "reveal_type(x)", K.REVEAL_MISMATCH, **rev)


def test_new_discrepancy_entries_have_runtime_override_off():
    for i in ("TY-4884", "MYPY-22339", "MYPY-20969", "MYPY-21937", "TY-876"):
        assert kb.BY_ID[f"UPSTREAM-{i}"].runtime_override is False


# priors ----------------------------------------------------------------------------------------------------------
def test_prior_mypy19889_caps_but_never_dismisses():
    s = src("bug-04-dataclasses-mypy-initvar-default-class-attr")
    attr = [("attr-defined", '"type[Sub]" has no attribute "extra"')]
    st, d = disc(s, "print(Sub.extra)", K.ONLY_MYPY, mypy=attr, pyright=[("reportAttributeAccessIssue", "Cannot access attribute")])
    assert "MYPY-19889" in {p.id for p in find_priors(s, d)}
    assert no_upstream(s, "print(Sub.extra)", K.ONLY_MYPY, mypy=attr)
    plain = "class A:\n    x: int = 0\n\n\nA.y\n"
    st, d = disc(plain, "A.y", K.ONLY_MYPY, mypy=[("attr-defined", '"type[A]" has no attribute "y"')])
    assert "MYPY-19889" not in {p.id for p in find_priors(plain, d)}


def test_prior_ty3765_ignores_union_annotations():
    s = "import enum\n\n\nclass I(enum.IntFlag):\n    A = 1\n\n\nx: int | None = None\nreveal_type(x)\n"
    st, d = disc(s, "x: int | None = None", K.REVEAL_MISMATCH, ty=[(None, "x")])
    assert "TY-3765" not in {p.id for p in find_priors(s, d)}


def test_prior_ty3765_intflag_is_related_only():
    s = "import enum\n\n\nclass I(enum.IntFlag):\n    A = 1\n\n\nv = int() & I.A\nreveal_type(v)\n"
    st, d = disc(s, "v = int() & I.A", K.REVEAL_MISMATCH, mypy=[(None, 'Revealed type is "int"')], ty=[(None, "x")])
    assert "TY-3765" in {p.id for p in find_priors(s, d)}
    assert no_upstream(s, "v = int() & I.A", K.REVEAL_MISMATCH, mypy=[(None, "x")], ty=[(None, "y")])
    st, d = disc(s.replace("IntFlag", "IntEnum"), "v = int() & I.A", K.REVEAL_MISMATCH, ty=[(None, "x")])
    assert "TY-3765" not in {p.id for p in find_priors(s.replace("IntFlag", "IntEnum"), d)}


def test_prior_ty4656_unchanged_and_not_duplicated():
    prior_ids = [p["id"] for p in RAW["prior_stances"]] + [e["id"] for e in RAW["entries"] if e.get("stance")]
    assert prior_ids.count("TY-4656") == 1
    p = next(p for p in RAW["prior_stances"] if p["id"] == "TY-4656")
    assert p["stance"] == "intended" and p["url"] == "https://github.com/astral-sh/ty/issues/4656"
    assert p["tags"] == ["self"] and p["kinds"] == ["only_mypy", "only_ty", "reveal_mismatch", "concern_mismatch", "runtime_miss"]


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
