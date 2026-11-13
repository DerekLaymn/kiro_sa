"""Day 7: dismissals for the known-duplicate shapes that the must-stay-live policy kept open until Day 6.

* TY-2171, TY-2171-ASSERT   ty folds a comparison with an instance of a tuple / NamedTuple subclass that defines the
                            dunder the comparison calls (open ty#2171, design in the closed ty#2140).
* TY-2792                   ty keeps the narrowing of ``obj.attr`` after ``obj.method()`` where the method assigns
                            ``self.attr`` (open ty#2792).
* TY-2792-READONLY          the ``Never`` row of the same cause: mypy rejects the assignment to a read-only property, ty
                            is silent because a stale narrowing made the statement unreachable.

Every positive has near-miss controls that must stay live; the end-to-end programs are in tests/test_stage3_round2.py and
tests/test_stage3_round3.py (calibration/known_duplicates/)."""
from __future__ import annotations

import pytest

from test_upstream_day6 import T_ASSERT, T_MYPY, T_TY, TUPLE, ids
from typediff.models import DiscrepancyKind as K


def fold_ids(src, stmt="reveal_type(r)", reveal=True):
    if reveal:
        return {i for i in ids(src, stmt, K.REVEAL_MISMATCH, mypy=T_MYPY, ty=T_TY) if "2171" in i}
    return {i for i in ids(src, stmt, K.ONLY_TY, ty=T_ASSERT) if "2171" in i}


# ------------------------------------------------------------------------------------------------ TY-2171


def test_tuple_subclass_override_is_closed_by_the_two_entries():
    assert fold_ids(TUPLE) == {"UPSTREAM-TY-2171"}
    assert fold_ids(TUPLE, "assert_type(r, bool)", reveal=False) == {"UPSTREAM-TY-2171-ASSERT"}


def test_tuple_subclass_forms_that_match():
    named = TUPLE.replace("class Restricted(tuple[Literal[1], Literal[2]]):", "class Restricted(NamedTuple):\n    a: int\n")
    assert fold_ids(named) == {"UPSTREAM-TY-2171"}
    direct = TUPLE.replace("r = pair == (3, 4)\nreveal_type(r)", "reveal_type(pair == (3, 4))")
    assert fold_ids(direct, "reveal_type(pair == (3, 4))") == {"UPSTREAM-TY-2171"}
    reflected = TUPLE.replace("r = pair == (3, 4)", "r = (3, 4) == pair")
    assert fold_ids(reflected) == {"UPSTREAM-TY-2171"}  # __eq__ is its own reflection
    ne = TUPLE.replace("__eq__", "__ne__").replace("pair == (3, 4)", "pair != (3, 4)")
    assert fold_ids(ne) == {"UPSTREAM-TY-2171"}
    lt = TUPLE.replace("__eq__", "__lt__").replace("pair == (3, 4)", "pair < (3, 4)")
    assert fold_ids(lt) == {"UPSTREAM-TY-2171"}
    gt_reflected = TUPLE.replace("__eq__", "__gt__").replace("pair == (3, 4)", "(3, 4) < pair")
    assert fold_ids(gt_reflected) == {"UPSTREAM-TY-2171"}  # (3, 4) < pair calls pair.__gt__
    inherited = TUPLE.replace("pair = Restricted((1, 2))", "class Sub(Restricted): ...\n\n\npair = Sub((1, 2))")
    assert fold_ids(inherited) == {"UPSTREAM-TY-2171"}
    annotated = TUPLE.replace("pair = Restricted((1, 2))\n", "def get(p: Restricted) -> bool:\n    return p == (3, 4)\n\n\n"
                              "pair = Restricted((1, 2))\n").replace("r = pair == (3, 4)", "r = get(pair) or pair == (3, 4)")
    assert fold_ids(annotated) == {"UPSTREAM-TY-2171"}


@pytest.mark.parametrize("name,src", [
    ("no override", TUPLE.replace("__eq__", "describe")),
    ("not a tuple", TUPLE.replace("tuple[Literal[1], Literal[2]]", "list[int]")),
    ("other dunder", TUPLE.replace("__eq__", "__lt__")),  # the comparison is ==
    ("reflected dunder missing", TUPLE.replace("__eq__", "__lt__").replace("pair == (3, 4)", "(3, 4) < pair")),
    ("__len__ only", TUPLE.replace("__eq__(self, other: object, /)", "__len__(self)")),
    ("plain tuples compared", TUPLE.replace("r = pair == (3, 4)", "r = (1, 2) == (3, 4)")),
    ("rebound to a plain tuple", TUPLE.replace("r = pair == (3, 4)", "pair = (1, 2)\nr = pair == (3, 4)")),
    ("other class instance", TUPLE.replace("r = pair == (3, 4)", "r = Other() == (3, 4)")
     .replace("pair = Restricted", "class Other: ...\n\n\npair = Restricted")),
])
def test_tuple_subclass_controls_stay_live(name, src):
    assert not fold_ids(src), name
    assert not fold_ids(src, "assert_type(r, bool)", reveal=False), name


def test_tuple_subclass_other_answers_stay_live():
    other_reveal = [("revealed-type", "Revealed type: `int`", "int")]
    assert not {i for i in ids(TUPLE, "reveal_type(r)", K.REVEAL_MISMATCH, mypy=T_MYPY, ty=other_reveal) if "2171" in i}
    other_assert = [("type-assertion-failure", "Type `int` does not match asserted type `bool`")]
    assert not {i for i in ids(TUPLE, "assert_type(r, bool)", K.ONLY_TY, ty=other_assert) if "2171" in i}
    wrong_asserted = [("type-assertion-failure", "Type `Literal[False]` does not match asserted type `int`")]
    assert not {i for i in ids(TUPLE, "assert_type(r, bool)", K.ONLY_TY, ty=wrong_asserted) if "2171" in i}
    mypy_side = [("assert-type", 'Expression is of type "Literal[False]", not "bool"')]
    assert not {i for i in ids(TUPLE, "assert_type(r, bool)", K.ONLY_MYPY, mypy=mypy_side) if "2171" in i}


# ------------------------------------------------------------------------------------------------ TY-2792

REV_MYPY = [(None, 'Revealed type is "int | None"', "int | None")]
REV_TY = [("revealed-type", "Revealed type: `int`", "int")]
CLASS_A = ("class A:\n    x: int | None = None\n\n    def clear(self) -> None:\n        self.x = None\n\n"
           "    def touch(self) -> None:\n        self.y = 1\n\n\n")


def stale_ids(body: str, stmt="reveal_type(a.x)", kind=K.REVEAL_MISMATCH):
    src = CLASS_A + "def f(a: A) -> None:\n" + "".join(f"    {ln}\n" for ln in body.splitlines())
    return {i for i in ids(src, stmt, kind, mypy=REV_MYPY, ty=REV_TY) if "2792" in i}


@pytest.mark.parametrize("body", [
    "a.x = 3\na.clear()\nreveal_type(a.x)",  # assignment narrowing
    "if a.x is None:\n    return\na.clear()\nreveal_type(a.x)",  # test narrowing
    "assert a.x is not None\na.clear()\nreveal_type(a.x)",
    "is_none = a.x is None\na.clear()\nif not is_none:\n    reveal_type(a.x)",  # aliased condition (calibration program)
    "has = isinstance(a.x, int)\na.clear()\nif has:\n    reveal_type(a.x)",
    "a.x = 3\nb = a\nb.clear()\nreveal_type(a.x)",  # the method is called through an alias of the receiver
    "a.x = 3\na.clear()\nreveal_type([a.x for _ in range(1)])",
    "a.x = 3\nprint('between')\na.clear()\nprint('later')\nreveal_type(a.x)",
])
def test_attribute_narrowing_kept_after_a_mutating_call(body):
    stmt = "reveal_type([a.x for _ in range(1)])" if "[a.x" in body else "reveal_type(a.x)"
    assert stale_ids(body, stmt) == {"UPSTREAM-TY-2792"}


def test_attribute_narrowing_on_self():
    src = (CLASS_A + "class B:\n    x: int | None = None\n\n    def reset(self) -> None:\n        self.x = None\n\n"
           "    def go(self) -> None:\n        self.x = 3\n        self.reset()\n        reveal_type(self.x)\n")
    assert {i for i in ids(src, "reveal_type(self.x)", K.REVEAL_MISMATCH, mypy=REV_MYPY, ty=REV_TY) if "2792" in i} \
        == {"UPSTREAM-TY-2792"}


@pytest.mark.parametrize("name,body", [
    ("no call", "a.x = 3\nreveal_type(a.x)"),
    ("call of a method that assigns another attribute", "a.x = 3\na.touch()\nreveal_type(a.x)"),
    ("call placed before the narrowing", "a.clear()\na.x = 3\nreveal_type(a.x)"),
    ("direct store after the call", "a.x = 3\na.clear()\na.x = 4\nreveal_type(a.x)"),
    ("receiver rebound after the call", "a.x = 3\na.clear()\na = A()\nreveal_type(a.x)"),
    ("call on another object", "a.x = 3\nb = A()\nb.clear()\nreveal_type(a.x)"),
    ("call is not a program method", "a.x = 3\na.append(1)\nreveal_type(a.x)"),
    ("never narrowed", "a.clear()\nreveal_type(a.x)"),
    ("other attribute is revealed", "a.x = 3\na.clear()\nreveal_type(a.y)"),
    # draft 2 of results/bugs.md: the reassignment reaches the use over the loop back edge
    ("loop back edge, no call", "is_none = a.x is None\nfor _ in range(2):\n    if not is_none:\n        reveal_type(a.x)\n    a.x = None"),
    ("loop back edge with a call", "is_none = a.x is None\nfor _ in range(2):\n    a.clear()\n    if not is_none:\n"
                                   "        reveal_type(a.x)\n    a.x = None"),
])
def test_attribute_narrowing_controls_stay_live(name, body):
    assert not stale_ids(body, "reveal_type(a.y)" if "a.y" in body else "reveal_type(a.x)"), name


def test_attribute_narrowing_only_for_reveal_rows():
    src = CLASS_A + "def f(a: A) -> None:\n    a.x = 3\n    a.clear()\n    reveal_type(a.x)\n"
    assert not {i for i in ids(src, "reveal_type(a.x)", K.ONLY_TY, ty=REV_TY) if "2792" in i}
    assert not {i for i in ids(src, "reveal_type(a.x)", K.ONLY_MYPY, mypy=REV_MYPY) if "2792" in i}


# ------------------------------------------------------------------------------------------------ TY-2792-READONLY

RO_MYPY = [("misc", 'Property "ro" defined in "T" is read-only')]
CLASS_T = ("class T:\n    def __init__(self, n: int) -> None:\n        self.n = n\n\n    def bump(self) -> None:\n"
           "        self.n += 1\n\n    @property\n    def ro(self) -> int:\n        return self.n\n\n    @property\n"
           "    def rw(self) -> int:\n        return self.n\n\n    @rw.setter\n    def rw(self, v: int) -> None:\n"
           "        self.n = v\n\n\n")


def ro_ids(body: str, stmt="t.ro = 1", mypy=RO_MYPY, kind=K.ONLY_MYPY):
    src = CLASS_T + "def f(t: T) -> None:\n" + "".join(f"    {ln}\n" for ln in body.splitlines())
    return {i for i in ids(src, stmt, kind, mypy=mypy) if "2792" in i}


@pytest.mark.parametrize("body", [
    "assert t.ro == 4\nt.bump()\nassert t.ro == 5\nt.ro = 1",  # contradictory asserts (the Day-6 programs)
    "if t.n != 8:\n    raise ValueError\nt.bump()\nif t.n != 9:\n    raise ValueError\nt.ro = 1",
    "assert t.ro == 3\nt.bump()\nlocal = t.ro\nt.ro = 1",
    "assert t.ro == 3\nu = t\nu.bump()\nlocal = t.ro\nt.ro = 1",
    "try:\n    assert t.ro == 3\n    t.bump()\n    assert t.ro == 4\n    t.ro = 1\nexcept AttributeError:\n    pass",
])
def test_readonly_property_after_stale_narrowing(body):
    assert ro_ids(body) == {"UPSTREAM-TY-2792-READONLY"}


@pytest.mark.parametrize("name,body", [
    ("property with a setter", "assert t.rw == 4\nt.bump()\nassert t.rw == 5\nt.rw = 1"),
    ("no method call", "assert t.ro == 4\nassert t.ro == 5\nt.ro = 1"),
    ("call placed before the narrowing", "t.bump()\nassert t.ro == 4\nassert t.ro == 5\nt.ro = 1"),
    ("no read after the call", "assert t.ro == 4\nt.bump()\nt.ro = 1"),
    ("store resets the narrowing", "assert t.n == 4\nt.bump()\nt.n = 7\nassert t.n == 7\nt.ro = 1"),
    ("receiver rebound", "assert t.ro == 4\nt.bump()\nt = T(1)\nassert t.ro == 5\nt.ro = 1"),
    ("call on another object", "assert t.ro == 4\nu = T(1)\nu.bump()\nassert t.ro == 5\nt.ro = 1"),
    ("not a program method", "assert t.ro == 4\nt.refresh()\nassert t.ro == 5\nt.ro = 1"),
    ("not a property", "assert t.n == 4\nt.bump()\nassert t.n == 5\nt.zzz = 1"),
])
def test_readonly_property_controls_stay_live(name, body):
    stmt = "t.rw = 1" if "t.rw = 1" in body else "t.zzz = 1" if "t.zzz" in body else "t.ro = 1"
    assert not ro_ids(body, stmt), name


def test_readonly_property_other_messages_and_kinds_stay_live():
    body = "assert t.ro == 4\nt.bump()\nassert t.ro == 5\nt.ro = 1"
    assert not ro_ids(body, mypy=[("misc", 'Cannot assign to a method')])
    assert not ro_ids(body, mypy=[("assignment", 'Property "ro" defined in "T" is read-only')])
    src = CLASS_T + "def f(t: T) -> None:\n" + "".join(f"    {ln}\n" for ln in body.splitlines())
    assert not {i for i in ids(src, "t.ro = 1", K.ONLY_TY, ty=RO_MYPY) if "2792" in i}
