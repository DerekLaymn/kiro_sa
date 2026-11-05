"""Day 6 morning: upstream entries added after reading the Day-6 reports (campaign/day6-report.md).

* TY-4756  mypy reports a method without ``self``; ty is silent (open lint request). A dismissal (DUPLICATE).
* TY-2171  ty folds comparisons of a tuple subclass that overrides a comparison dunder. A PRIOR STANCE (Day 6); since
           Day 7 the narrow comparison-dunder shape is also closed by the dismissals TY-2171 / TY-2171-ASSERT
           (tests/test_upstream_day7.py), the prior stance covers the rest (``__len__`` / ``__bool__``).

Every positive has controls that must stay live."""
from __future__ import annotations

from typediff.kb import matching_entries
from typediff.models import Diagnostic, Discrepancy, DiscrepancyKind as K, RuntimeResult, Severity, Tool
from typediff.priors import find_priors
from typediff.state import CaseState


def dg(tool, line, code, msg, reveal=None):
    return Diagnostic(tool, line, 1, Severity.NOTE if reveal else Severity.ERROR, code, msg, revealed_type=reveal)


def disc(source: str, stmt: str, kind: K, mypy=(), ty=(), relation=None):
    ln = next(i for i, x in enumerate(source.splitlines(), 1) if stmt in x)
    m = [dg(Tool.MYPY, ln, *x) for x in mypy]
    t = [dg(Tool.TY, ln, *x) for x in ty]
    d = Discrepancy("D1", kind, ln, ln, stmt, "", mypy=m, ty=t, pyright=[], reveal_relation=relation)
    st = CaseState("t", source, "3.13", {Tool.MYPY: m, Tool.TY: t, Tool.PYRIGHT: []},
                   RuntimeResult(status="success"), [], {}, {}, pyright_ran=True)
    return st, d


def ids(source: str, stmt: str, kind: K, **kw) -> set[str]:
    st, d = disc(source, stmt, kind, **kw)
    return {e.id for e in matching_entries(st, d)}


def priors(source: str, stmt: str, kind: K, **kw) -> set[str]:
    _, d = disc(source, stmt, kind, **kw)
    return {p.id for p in find_priors(source, d)}


# ------------------------------------------------------------------------------------------------ TY-4756
SELF = ("from collections.abc import Callable\n\n\nclass Field:\n    def passthrough(fn: Callable[..., None]) -> Callable[..., None]:\n"
        "        return fn\n\n    @passthrough\n    def __set__(self, instance: object, value: int) -> None:\n        print(value)\n")
SELF_MYPY = [("misc", '"self" parameter missing for a non-static method (or an invalid type for self)')]


def test_missing_self_is_ty_4756():
    assert "UPSTREAM-TY-4756" in ids(SELF, "def passthrough", K.ONLY_MYPY, mypy=SELF_MYPY)


def test_missing_self_controls_stay_live():
    other = [("misc", 'Self argument missing for a non-static method (or an invalid type for self)')]
    assert "UPSTREAM-TY-4756" not in ids(SELF, "def passthrough", K.ONLY_MYPY, mypy=other)
    other_code = [("attr-defined", '"self" parameter missing for a non-static method')]
    assert "UPSTREAM-TY-4756" not in ids(SELF, "def passthrough", K.ONLY_MYPY, mypy=other_code)
    assert "UPSTREAM-TY-4756" not in ids(SELF, "def passthrough", K.ONLY_TY, ty=SELF_MYPY)  # wrong kind


# ------------------------------------------------------------------------------------------------ TY-2171 (prior stance)
TUPLE = ("from typing import Literal, assert_type, reveal_type\n\n\n"
         "class Restricted(tuple[Literal[1], Literal[2]]):\n    def __eq__(self, other: object, /) -> bool:\n"
         "        return True\n\n\npair = Restricted((1, 2))\nr = pair == (3, 4)\nreveal_type(r)\nassert_type(r, bool)\n")
T_MYPY = [(None, 'Revealed type is "bool"', "bool")]
T_TY = [("revealed-type", "Revealed type: `Literal[False]`", "Literal[False]")]
T_ASSERT = [("type-assertion-failure", "Type `Literal[False]` does not match asserted type `bool`")]


def test_tuple_subclass_override_has_prior_stance_and_the_comparison_shape_is_closed():
    assert "TY-2171-PRIOR" in priors(TUPLE, "reveal_type(r)", K.REVEAL_MISMATCH, mypy=T_MYPY, ty=T_TY)
    assert "TY-2171-PRIOR" in priors(TUPLE, "assert_type(r, bool)", K.ONLY_TY, ty=T_ASSERT)
    named = TUPLE.replace("class Restricted(tuple[Literal[1], Literal[2]]):", "class Restricted(NamedTuple):\n    a: int\n")
    assert "TY-2171-PRIOR" in priors(named, "reveal_type(r)", K.REVEAL_MISMATCH, mypy=T_MYPY, ty=T_TY)
    # Day 7 decision: the narrow comparison-dunder shape is ALSO closed by the dismissals TY-2171 / TY-2171-ASSERT
    # (tests/test_upstream_day7.py); the prior stance stays for the shapes those dismissals do not match
    assert [i for i in ids(TUPLE, "reveal_type(r)", K.REVEAL_MISMATCH, mypy=T_MYPY, ty=T_TY) if "2171" in i] == ["UPSTREAM-TY-2171"]
    assert [i for i in ids(TUPLE, "assert_type(r, bool)", K.ONLY_TY, ty=T_ASSERT) if "2171" in i] == ["UPSTREAM-TY-2171-ASSERT"]
    len_only = TUPLE.replace("__eq__(self, other: object, /)", "__len__(self)")
    assert "TY-2171-PRIOR" in priors(len_only, "reveal_type(r)", K.REVEAL_MISMATCH, mypy=T_MYPY, ty=T_TY)
    assert not [i for i in ids(len_only, "reveal_type(r)", K.REVEAL_MISMATCH, mypy=T_MYPY, ty=T_TY) if "2171" in i]


def test_tuple_subclass_prior_controls():
    no_override = TUPLE.replace("__eq__", "describe")
    assert "TY-2171-PRIOR" not in priors(no_override, "reveal_type(r)", K.REVEAL_MISMATCH, mypy=T_MYPY, ty=T_TY)
    not_tuple = TUPLE.replace("tuple[Literal[1], Literal[2]]", "list[int]")
    assert "TY-2171-PRIOR" not in priors(not_tuple, "reveal_type(r)", K.REVEAL_MISMATCH, mypy=T_MYPY, ty=T_TY)
    other_reveal = [("revealed-type", "Revealed type: `int`", "int")]
    assert "TY-2171-PRIOR" not in priors(TUPLE, "reveal_type(r)", K.REVEAL_MISMATCH, mypy=T_MYPY, ty=other_reveal)
