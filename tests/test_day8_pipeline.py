"""Day 8 phase 1: KB matchers for known duplicates and display noise, and the runtime-evidence fixes.

KB (every positive has controls that must stay live):

* TY-2792 / TY-2792-READONLY   a store into a data-descriptor attribute runs ``__set__``, which changes the owner's
                               attributes: the same stale narrowing as a mutating method call (D7-3).
* MYPY-2455 / TY-4941          a class with ``__eq__`` and no ``__hash__`` is accepted for ``Hashable`` (pyright rejects;
                               mypy and ty are silent) (H1).
* PYRIGHT-11382                class access to a data descriptor that is also assigned on the instance (D7-4).
* TY-3666                      mypy "erased type of self is not a supertype", ty accepts the annotation.
* CALLABLE-SELF-ATTR-STORE, CALLABLE-SELF-RECEIVER   the ParamSpec ``self: Callable[P, T]`` family.
* DISPLAY-EQUIVALENT           callable / ParamSpec-scope / TypedDict spellings of the same type.

Pipeline: caught exceptions as ``only_pyright`` evidence, ``runtime_miss`` after an ``# expect-error`` line, mypy's ``...``
in a recursive alias."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from test_upstream_day6 import dg, ids
from typediff.anchors import AnchorMap
from typediff.discrepancy import find_discrepancies, handled_type_exception, pyright_runtime_relation
from typediff.display import defaults_match, display_canon
from typediff.kb import matching_entries
from typediff.models import (
    Discrepancy, DiscrepancyKind as K, RuntimeProbe, RuntimeResult, Severity, Tool,
)
from typediff.models import Diagnostic
from typediff.rules import attach_pyright_evidence, attach_runtime_evidence, recursive_aliases
from typediff.state import CaseState


def pids(source: str, stmt: str, kind: K, mypy=(), ty=(), pyright=()) -> set[str]:
    """Entry ids that match, with pyright diagnostics (``(code, message)``) on the statement line."""
    ln = next(i for i, x in enumerate(source.splitlines(), 1) if stmt in x)
    m = [dg(Tool.MYPY, ln, *x) for x in mypy]
    t = [dg(Tool.TY, ln, *x) for x in ty]
    p = [dg(Tool.PYRIGHT, ln, *x) for x in pyright]
    d = Discrepancy("D1", kind, ln, ln, stmt, "", mypy=m, ty=t, pyright=p)
    st = CaseState("t", source, "3.13", {Tool.MYPY: m, Tool.TY: t, Tool.PYRIGHT: p}, RuntimeResult(status="success"), [], {}, {},
                   pyright_ran=True)
    return {e.id for e in matching_entries(st, d)}


# ------------------------------------------------------------------------------------------------ D7-3 descriptor store
DESCR = ("class Bumper:\n    def __set__(self, obj: 'Thing', value: int) -> None:\n        obj.base += value\n\n\n"
         "class Quiet:\n    def __set__(self, obj: 'Thing', value: int) -> None:\n        print(value)\n\n\n"
         "class NotData:\n    def __get__(self, obj: object, owner: type) -> int:\n        return 1\n\n\n"
         "class Thing:\n    bumped = Bumper()\n    quiet = Quiet()\n    plain = NotData()\n\n"
         "    def __init__(self, base: int) -> None:\n        self.base = base\n        self.other = 0\n\n"
         "    @property\n    def ro(self) -> int:\n        return self.base\n\n\n")
RO_MYPY = [("misc", 'Property "ro" defined in "Thing" is read-only')]
REV_MYPY = [(None, 'Revealed type is "int | None"', "int | None")]
REV_TY = [("revealed-type", "Revealed type: `int`", "int")]


def ro_ids(body: str, stmt="t.ro = 1"):
    src = DESCR + "def f(t: Thing) -> None:\n" + "".join(f"    {ln}\n" for ln in body.splitlines())
    return {i for i in ids(src, stmt, K.ONLY_MYPY, mypy=RO_MYPY) if "2792" in i}


def rev_ids(body: str, stmt="reveal_type(t.base)"):
    src = DESCR + "def f(t: Thing) -> None:\n" + "".join(f"    {ln}\n" for ln in body.splitlines())
    return {i for i in ids(src, stmt, K.REVEAL_MISMATCH, mypy=REV_MYPY, ty=REV_TY) if "2792" in i}


@pytest.mark.parametrize("body", [
    "assert t.base == 4\nt.bumped = 3\nassert t.base == 7\nt.ro = 1",  # the Day-7 mutant
    "if t.base != 4:\n    raise ValueError\nt.bumped = 3\nif t.base != 7:\n    raise ValueError\nt.ro = 1",
    "assert t.base == 4\nu = t\nu.bumped = 3\nlocal = t.base\nt.ro = 1",  # through an alias of the receiver
    "assert t.base == 4\ntry:\n    t.bumped = 3\n    assert t.base == 7\n    t.ro = 1\nexcept AttributeError:\n    pass",
])
def test_descriptor_store_keeps_the_readonly_property_row_closed(body):
    assert ro_ids(body) == {"UPSTREAM-TY-2792-READONLY"}


@pytest.mark.parametrize("name,body", [
    ("descriptor __set__ assigns nothing on the owner", "assert t.base == 4\nt.quiet = 3\nassert t.base == 7\nt.ro = 1"),
    ("non-descriptor attribute store", "assert t.base == 4\nt.other = 3\nassert t.base == 7\nt.ro = 1"),
    ("non-data descriptor (no __set__)", "assert t.base == 4\nt.plain = 3\nassert t.base == 7\nt.ro = 1"),
    ("store before the narrowing", "t.bumped = 3\nassert t.base == 4\nassert t.base == 7\nt.ro = 1"),
    ("no read after the store", "assert t.base == 4\nt.bumped = 3\nt.ro = 1"),
    ("receiver rebound after the store", "assert t.base == 4\nt.bumped = 3\nt = Thing(1)\nassert t.base == 7\nt.ro = 1"),
    ("store on another object", "assert t.base == 4\nu = Thing(1)\nu.bumped = 3\nassert t.base == 7\nt.ro = 1"),
    ("direct store resets the narrowing", "assert t.base == 4\nt.bumped = 3\nt.base = 9\nassert t.base == 9\nt.ro = 1"),
])
def test_descriptor_store_controls_stay_live(name, body):
    assert not ro_ids(body), name


def test_descriptor_store_also_closes_the_stale_reveal_row():
    # c3r.py of Day 7: ty reveals Literal[4] for t.base after the descriptor store, as after a plain method call
    assert rev_ids("assert t.base == 4\nt.bumped = 3\nreveal_type(t.base)") == {"UPSTREAM-TY-2792"}
    assert not rev_ids("assert t.base == 4\nt.quiet = 3\nreveal_type(t.base)")
    assert not rev_ids("assert t.base == 4\nt.other = 3\nreveal_type(t.base)")


# ------------------------------------------------------------------------------------------------ H1 Hashable
HASH = ("from collections.abc import Hashable\n\n\nclass Plain:\n    def __eq__(self, value: object) -> bool:\n        return True\n\n\n"
        "class Sub(Plain): ...\n\n\nclass Keyed(Plain):\n    def __hash__(self) -> int:\n        return 1\n\n\n"
        "class Other(Plain):\n    def __eq__(self, value: object) -> bool:\n        return False\n\n\n"
        "class Ext(dict):\n    def __eq__(self, value: object) -> bool:\n        return True\n\n\n"
        "class Setter(Plain):\n    __hash__ = object.__hash__\n\n\n"
        "def need(x: Hashable) -> int:\n    return hash(x)\n\n\n")


def hash_ids(call: str, msg_type: str, param="Hashable", kind=K.ONLY_PYRIGHT, code="reportArgumentType"):
    src = HASH + call + "\n"
    msg = f'Argument of type "{msg_type}" cannot be assigned to parameter "x" of type "{param}" in function "need"'
    return {i for i in pids(src, call, kind, pyright=[(code, msg)]) if "2455" in i or "4941" in i}


@pytest.mark.parametrize("call,typ", [
    ("need(Plain())", "Plain"), ("need(Sub())", "Sub"), ("need(Other())", "Other"), ("need(Plain() if True else Sub())", "Plain | Sub"),
])
def test_eq_without_hash_for_hashable_is_closed_by_both_entries(call, typ):
    assert hash_ids(call, typ) == {"UPSTREAM-MYPY-2455", "UPSTREAM-TY-4941"}


@pytest.mark.parametrize("name,call,typ,kw", [
    ("class with its own __hash__", "need(Keyed())", "Keyed", {}),
    ("__hash__ assigned in the class body", "need(Setter())", "Setter", {}),
    ("external base", "need(Ext())", "Ext", {}),
    ("a member of the union is hashable", "need(Keyed() if True else Plain())", "Keyed | Plain", {}),
    ("not a program class", "need(Plain())", "Missing", {}),
    ("another parameter type", "need(Plain())", "Plain", {"param": "Sized"}),
    ("another pyright rule", "need(Plain())", "Plain", {"code": "reportCallIssue"}),
    ("not an only_pyright finding", "need(Plain())", "Plain", {"kind": K.ONLY_TY}),
])
def test_eq_without_hash_controls_stay_live(name, call, typ, kw):
    assert not hash_ids(call, typ, **kw), name


def test_dataclass_is_not_judged():
    src = HASH.replace("class Other(Plain):", "from dataclasses import dataclass\n\n\n@dataclass\nclass Rec:\n    a: int\n\n\nclass Other(Plain):")
    call = "need(Rec(1))"
    msg = 'Argument of type "Rec" cannot be assigned to parameter "x" of type "Hashable" in function "need"'
    got = pids(src + call + "\n", call, K.ONLY_PYRIGHT, pyright=[("reportArgumentType", msg)])
    assert not {i for i in got if "2455" in i or "4941" in i}


# ------------------------------------------------------------------------------------------------ D7-4 pyright#11382
GAUGE = ("from typing import assert_type\n\n\nclass Clamped:\n    def __get__(self, instance: object, owner: type) -> int:\n"
         "        return 0\n\n    def __set__(self, instance: object, value: int) -> None:\n        pass\n\n\n"
         "class Frozen:\n    def __get__(self, instance: object, owner: type) -> int:\n        return 0\n\n\n"
         "class Gauge:\n    level = Clamped()\n    fixed = Clamped()\n    ro = Frozen()\n\n    def __init__(self, start: int) -> None:\n"
         "        self.level = start\n        self.ro = start\n\n\n")
PYR = ('reportAssertTypeFailure', '"assert_type" mismatch: expected "Clamped" but received "Clamped | int"')


def gauge_ids(stmt: str, msg=PYR, kind=K.ONLY_PYRIGHT, src=GAUGE):
    return {i for i in pids(src + stmt + "\n", stmt, kind, pyright=[msg]) if "11382" in i}


def test_class_access_of_a_descriptor_assigned_on_the_instance():
    assert gauge_ids("assert_type(Gauge.level, Clamped)") == {"UPSTREAM-PYRIGHT-11382"}


@pytest.mark.parametrize("name,stmt,kw", [
    ("descriptor never assigned on the instance", "assert_type(Gauge.fixed, Clamped)", {}),
    ("non-data descriptor", "assert_type(Gauge.ro, Frozen)", {"msg": ('reportAssertTypeFailure', '"assert_type" mismatch: expected "Frozen" but received "Frozen | int"')}),
    ("instance access", "assert_type(Gauge(1).level, int)", {}),
    ("message without a union", "assert_type(Gauge.level, Clamped)", {"msg": ('reportAssertTypeFailure', '"assert_type" mismatch: expected "Clamped" but received "int"')}),
    ("union does not name the descriptor", "assert_type(Gauge.level, Clamped)", {"msg": ('reportAssertTypeFailure', '"assert_type" mismatch: expected "Clamped" but received "str | int"')}),
    ("another pyright rule", "assert_type(Gauge.level, Clamped)", {"msg": ('reportAttributeAccessIssue', 'received "Clamped | int"')}),
    ("not an only_pyright finding", "assert_type(Gauge.level, Clamped)", {"kind": K.ONLY_TY}),
])
def test_descriptor_controls_stay_live(name, stmt, kw):
    assert not gauge_ids(stmt, **kw), name


def test_descriptor_without_instance_assignment_in_any_method():
    src = GAUGE.replace("        self.level = start\n", "        pass\n")
    assert not gauge_ids("assert_type(Gauge.level, Clamped)", src=src)


# ------------------------------------------------------------------------------------------------ TY-3666
SELF_MYPY = [("misc", 'The erased type of self "def (int) -> int" is not a supertype of its class "case.Job"')]
JOB = "from typing import Callable\n\n\nclass Job:\n    def run(self: Callable[[int], int], x: int) -> int:\n        return self(x)\n"


def test_self_annotation_not_a_supertype_is_ty_3666():
    assert "UPSTREAM-TY-3666" in ids(JOB, "def run", K.ONLY_MYPY, mypy=SELF_MYPY)


def test_self_annotation_controls():
    other = [("misc", 'Self argument missing for a non-static method (or an invalid type for self)')]
    assert "UPSTREAM-TY-3666" not in ids(JOB, "def run", K.ONLY_MYPY, mypy=other)
    assert "UPSTREAM-TY-3666" not in ids(JOB, "def run", K.ONLY_MYPY, mypy=[("attr-defined", SELF_MYPY[0][1])])
    assert "UPSTREAM-TY-3666" not in ids(JOB, "def run", K.ONLY_TY, ty=SELF_MYPY)  # wrong kind


# ------------------------------------------------------------------------------------------------ ParamSpec family
FAM = ("from typing import Callable, Concatenate, ParamSpec, TypeVar, reveal_type\n\nT = TypeVar('T')\nP = ParamSpec('P')\n\n\n"
       "class User:\n    def __init__(self: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> None:\n"
       "        self.args = args\n        other = 1\n        other.real = 2\n\n"
       "    @classmethod\n    def __call__(cls: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:\n        raise NotImplementedError\n\n\n"
       "class Plain:\n    def __init__(self, x: int) -> None:\n        self.x = x\n\n    def go(self) -> None:\n        self.y = 1\n\n\n"
       "u = User()\nUser.__call__(1)\nu(4, 5)\nPlain(1).go()\n\n\n"
       "def probe(w: User) -> None:\n    made = w()\n    reveal_type(made)\n    reveal_type(Plain(1))\n    reveal_type(u.args)\n")
TY_ATTR = [("unresolved-attribute", "Unresolved attribute `args` on type `(int, /, *args: P@__init__.args, **kwargs: P@__init__.kwargs) -> T@__init__`")]
PY_ATTR = [("reportFunctionMemberAccess", 'Cannot assign to attribute "args" for class "FunctionType"')]


def fam_ids(stmt, kind, **kw):
    return {i for i in pids(FAM, stmt, kind, **kw) if i.startswith("CALLABLE-SELF")}


def test_attribute_store_on_a_callable_annotated_self():
    assert fam_ids("self.args = args", K.ONLY_TY, ty=TY_ATTR, pyright=PY_ATTR) >= {"CALLABLE-SELF-ATTR-STORE"}
    assert "CALLABLE-SELF-ATTR-STORE" in fam_ids("self.args = args", K.ONLY_PYRIGHT, pyright=PY_ATTR)


@pytest.mark.parametrize("name,stmt,kind,kw", [
    ("store on another name", "other.real = 2", K.ONLY_TY, {"ty": TY_ATTR}),
    ("receiver is not annotated", "self.y = 1", K.ONLY_TY, {"ty": TY_ATTR}),
    ("another ty rule", "self.args = args", K.ONLY_TY, {"ty": [("invalid-assignment", "Object of type `int` is not assignable")]}),
    ("another pyright rule", "self.args = args", K.ONLY_PYRIGHT, {"pyright": [("reportAttributeAccessIssue", "Cannot assign")]}),
    ("ty message not about a callable type", "self.args = args", K.ONLY_TY, {"ty": [("unresolved-attribute", "Unresolved attribute `args` on type `User`")]}),
    ("wrong kind", "self.args = args", K.REVEAL_MISMATCH, {"ty": TY_ATTR}),
])
def test_attribute_store_controls_stay_live(name, stmt, kind, kw):
    assert "CALLABLE-SELF-ATTR-STORE" not in fam_ids(stmt, kind, **kw), name


CALL_TY = [("invalid-argument-type", "Argument to bound method `User.__call__` is incorrect: Expected `P@__init__.args`, found `Literal[1]`")]


@pytest.mark.parametrize("stmt", ["User.__call__(1)", "u = User()", "u(4, 5)", "def __init__(self: Callable[P, T]", "self.args = args"])
def test_statements_around_a_callable_annotated_receiver(stmt):
    assert "CALLABLE-SELF-RECEIVER" in fam_ids(stmt, K.ONLY_TY, ty=CALL_TY)
    assert "CALLABLE-SELF-RECEIVER" in fam_ids(stmt, K.ONLY_PYRIGHT, pyright=[("reportCallIssue", "Expected 0 positional arguments")])


def test_parameters_and_derived_variables_of_the_class():
    assert "CALLABLE-SELF-RECEIVER" in fam_ids("made = w()", K.CONCERN_MISMATCH,
                                               mypy=[("var-annotated", 'Need type annotation for "made"')], ty=CALL_TY)
    reveal = dict(mypy=[(None, 'Revealed type is "Any"', "Any")], ty=[("revealed-type", "Revealed type: `() -> T`", "() -> T")])
    assert "CALLABLE-SELF-RECEIVER" in fam_ids("reveal_type(made)", K.REVEAL_MISMATCH, **reveal)  # made = w(), w: User


STATIC = ("from typing import Callable\n\n\nclass Pipe:\n    @staticmethod\n    def compose(f: Callable[[int], int], g: Callable[[int], int]) -> int:\n"
          "        return f(g(1))\n\n    @classmethod\n    def build(cls, f: Callable[[int], int]) -> int:\n        return f(1)\n\n"
          "    def run(self, f: Callable[[int], int]) -> int:\n        return f(1)\n\n\n"
          "p = Pipe()\nPipe.compose(1, 2)\np.run(3)\nPipe.build(4)\nself_like = Pipe\n")


@pytest.mark.parametrize("stmt", ["Pipe.compose(1, 2)", "p.run(3)", "Pipe.build(4)", "p = Pipe()", "return f(g(1))", "def compose"])
@pytest.mark.parametrize("kind,kw", [(K.ONLY_TY, {"ty": CALL_TY}), (K.ONLY_MYPY, {"mypy": [("arg-type", "bad")]}),
                                     (K.ONLY_PYRIGHT, {"pyright": [("reportCallIssue", "bad")]})])
def test_a_callable_parameter_after_self_or_a_staticmethod_is_no_receiver(stmt, kind, kw):
    # review finding: the first parameter of a @staticmethod (and any later parameter) is an ordinary Callable argument
    got = {i for i in pids(STATIC, stmt, kind, **kw) if i.startswith("CALLABLE-SELF")}
    assert not got, got


def test_a_staticmethod_next_to_a_real_receiver_does_not_widen_the_entry():
    src = STATIC + "\n\nclass Real:\n    @classmethod\n    def __call__(cls: Callable[[int], int], x: int) -> int:\n        return x\n"
    assert "CALLABLE-SELF-RECEIVER" in {i for i in pids(src, "def __call__", K.ONLY_TY, ty=CALL_TY)}
    assert not {i for i in pids(src, "Pipe.compose(1, 2)", K.ONLY_TY, ty=CALL_TY) if i.startswith("CALLABLE-SELF")}


def test_statements_that_touch_no_such_class_stay_live():
    assert "CALLABLE-SELF-RECEIVER" not in fam_ids("Plain(1).go()", K.ONLY_TY, ty=CALL_TY)
    assert "CALLABLE-SELF-RECEIVER" not in fam_ids("self.y = 1", K.ONLY_TY, ty=CALL_TY)
    reveal = dict(mypy=[(None, 'Revealed type is "int"', "int")], ty=[("revealed-type", "Revealed type: `str`", "str")])
    assert "CALLABLE-SELF-RECEIVER" not in fam_ids("reveal_type(Plain(1))", K.REVEAL_MISMATCH, **reveal)
    plain = FAM.replace("Callable[P, T]", "'User'")
    assert "CALLABLE-SELF-RECEIVER" not in {i for i in pids(plain, "User.__call__(1)", K.ONLY_TY, ty=CALL_TY)}


def test_a_pure_spelling_difference_is_closed_as_display_noise_before_the_receiver_entry():
    from typediff.kb import matching_entries as me

    ln = next(i for i, x in enumerate(FAM.splitlines(), 1) if "reveal_type(u.args)" in x)
    m = [dg(Tool.MYPY, ln, None, 'Revealed type is "P.args"', "P.args")]
    t = [dg(Tool.TY, ln, "revealed-type", "Revealed type: `P@__init__.args`", "P@__init__.args")]
    d = Discrepancy("D1", K.REVEAL_MISMATCH, ln, ln, "reveal_type(u.args)", "", mypy=m, ty=t, pyright=[])
    st = CaseState("t", FAM, "3.13", {Tool.MYPY: m, Tool.TY: t, Tool.PYRIGHT: []}, RuntimeResult(status="success"), [], {}, {},
                   pyright_ran=True)
    order = [e.id for e in me(st, d) if e.id.startswith(("DISPLAY", "CALLABLE"))]
    assert order == ["DISPLAY-EQUIVALENT", "CALLABLE-SELF-RECEIVER"]


def test_cpython_type_error_at_a_receiver_statement_keeps_it_in_review():
    from typediff.kb import entry_demotion, BY_ID

    ln = next(i for i, x in enumerate(FAM.splitlines(), 1) if "User.__call__(1)" in x)
    t = [dg(Tool.TY, ln, *CALL_TY[0])]
    d = Discrepancy("D1", K.ONLY_TY, ln, ln, "User.__call__(1)", "", mypy=[], ty=t, pyright=[])
    rt = RuntimeResult(status="exception", exc_type="TypeError", exc_message="takes 1 positional argument but 2 were given",
                       exc_line=ln, frames=[(ln, "<module>")], executed_lines=[ln])
    st = CaseState("t", FAM, "3.13", {Tool.MYPY: [], Tool.TY: t, Tool.PYRIGHT: []}, rt, [], {}, {}, pyright_ran=True)
    assert entry_demotion(st, d, BY_ID["CALLABLE-SELF-RECEIVER"]) is not None


# ------------------------------------------------------------------------------------------------ display noise
TD = ("from typing import TypedDict\n\n\nclass Options(TypedDict, total=False):\n    verbose: bool\n\n\nclass NotTD:\n    a: int\n\n\n"
      "def f(kwargs: Options) -> None:\n    reveal_type(kwargs)\n    reveal_type(NotTD)\n")


def disp_ids(src, stmt, mypy_rev, ty_rev, pyright_rev=None):
    ln = next(i for i, x in enumerate(src.splitlines(), 1) if stmt in x)
    m = [dg(Tool.MYPY, ln, None, f'Revealed type is "{mypy_rev}"', mypy_rev)]
    t = [dg(Tool.TY, ln, "revealed-type", f"Revealed type: `{ty_rev}`", ty_rev)]
    p = [dg(Tool.PYRIGHT, ln, None, f'Type of "x" is "{pyright_rev}"', pyright_rev)] if pyright_rev else []
    d = Discrepancy("D1", K.REVEAL_MISMATCH, ln, ln, stmt, "", mypy=m, ty=t, pyright=p, reveal_relation="uncomparable")
    st = CaseState("t", src, "3.13", {Tool.MYPY: m, Tool.TY: t, Tool.PYRIGHT: p}, RuntimeResult(status="success"), [], {}, {},
                   pyright_ran=True)
    return {e.id for e in matching_entries(st, d)}


@pytest.mark.parametrize("mypy_rev,ty_rev,pyr", [
    ("TypedDict(case.Options, {'verbose'?: bool})", "Options", "Options"),
    ("def (float)", "(float, /) -> None", "(float) -> None"),
    ("tuple[def (list[int]), ...]", "tuple[(list[int], /) -> None, ...]", "tuple[(list[int]) -> None, ...]"),
    ("def (self: case.Child, a: int, b: int =, *, c: int) -> None", "(self: Child, a: int, b: int = 0, *, c: int) -> None",
     "(self: Child, a: int, b: int = 0, *, c: int) -> None"),
    ("P.args", "P@__init__.args", "P@__init__.args"),
    ("case.Runner[[name: str, *, upper: bool =], str]", "Runner[(name: str, *, upper: bool = False), str]",
     "Runner[(name: str, *, upper: bool = False), str]"),
    ("def [P, R] (f: def (int, *P.args, **P.kwargs) -> R) -> def (*P.args, **P.kwargs) -> R",
     "[**P, R](f: (int, /, *args: P.args, **kwargs: P.kwargs) -> R) -> ((**P) -> R)",
     "(f: (int, **P@with_tag) -> R@with_tag) -> ((**P@with_tag) -> R@with_tag)"),
])
def test_display_only_differences_are_noise(mypy_rev, ty_rev, pyr):
    assert "DISPLAY-EQUIVALENT" in disp_ids(TD, "reveal_type(kwargs)", mypy_rev, ty_rev, pyr)
    assert "DISPLAY-EQUIVALENT" in disp_ids(TD, "reveal_type(kwargs)", mypy_rev, ty_rev)  # pyright silent


@pytest.mark.parametrize("name,mypy_rev,ty_rev,pyr", [
    ("different return type", "def (int) -> str", "(int, /) -> int", "(int) -> int"),
    ("different parameter name", "def (a: int)", "(b: int) -> None", "(b: int) -> None"),
    ("default presence", "def (a: int =)", "(a: int) -> None", "(a: int) -> None"),
    ("different parameter type", "def (a: int)", "(a: str) -> None", "(a: str) -> None"),
    ("positional-only vs named", "def (a: int)", "(int, /) -> None", "(int) -> None"),
    ("different ParamSpec", "def (*P.args, **P.kwargs) -> int", "(**Q) -> int", "(**Q) -> int"),
    ("TypedDict of another name", "TypedDict(case.Options, {'verbose'?: bool})", "Other", "Other"),
    ("pyright says something else", "def (float)", "(float, /) -> None", "(float) -> int"),
    ("plain difference", "int", "str", "str"),
    ("ParamSpec argument with another parameter", "case.Runner[[name: str], str]", "Runner[(label: str), str]", "Runner[(label: str), str]"),
    ("ParamSpec argument with another default presence", "case.Runner[[name: str =], str]", "Runner[(name: str), str]", "Runner[(name: str), str]"),
])
def test_display_controls_stay_live(name, mypy_rev, ty_rev, pyr):
    assert "DISPLAY-EQUIVALENT" not in disp_ids(TD, "reveal_type(kwargs)", mypy_rev, ty_rev, pyr), name


def test_a_default_value_that_differs_between_ty_and_pyright_is_not_display_noise():
    # review finding 4 (user decision: option c): ty and pyright are compared WITH default values
    mypy = "def (a: int =)"
    assert "DISPLAY-EQUIVALENT" in disp_ids(TD, "reveal_type(kwargs)", mypy, "(a: int = 1) -> None", "(a: int = 1) -> None")
    for pyr in ("(a: int = 2) -> None", "(a: int = None) -> None", "(a: int) -> None"):  # real mismatch / missing default
        assert "DISPLAY-EQUIVALENT" not in disp_ids(TD, "reveal_type(kwargs)", mypy, "(a: int = 1) -> None", pyr), pyr
    # only the mismatching parameter matters, in any position
    assert "DISPLAY-EQUIVALENT" not in disp_ids(TD, "reveal_type(kwargs)", "def (a: int =, b: str =)",
                                                "(a: int = 1, b: str = 'x') -> None", "(a: int = 1, b: str = 'y') -> None")


FACTORY = ("from dataclasses import dataclass, field\nfrom typing import reveal_type\n\n\n@dataclass\nclass Child:\n"
           "    a: int = 0\n    names: list[str] = field(default_factory=list)\n\n\nreveal_type(Child.__init__)\n")
FACTORY_M = "def (self: case.Child, a: int =, names: list[str] =)"
FACTORY_T = "(self: Child, a: int = 0, names: list[str] = ...) -> None"


def test_default_factory_reveal_stays_display_noise():
    # ty prints `...` and pyright the factory name for a default_factory default
    assert "DISPLAY-EQUIVALENT" in disp_ids(FACTORY, "reveal_type(Child", FACTORY_M, FACTORY_T,
                                            "(self: Child, a: int = 0, names: list[str] = list) -> None")
    assert "DISPLAY-EQUIVALENT" in disp_ids(FACTORY, "reveal_type(Child", FACTORY_M, FACTORY_T,
                                            "(self: Child, a: int = 0, names: list[str] = ...) -> None")


def test_default_factory_reveal_controls():
    # a real mismatch next to a factory default is still a difference
    assert "DISPLAY-EQUIVALENT" not in disp_ids(FACTORY, "reveal_type(Child", FACTORY_M, FACTORY_T,
                                                "(self: Child, a: int = 5, names: list[str] = list) -> None")
    # a name that the program does not pass as default_factory is no wildcard against a printed value
    assert "DISPLAY-EQUIVALENT" not in disp_ids(TD, "reveal_type(kwargs)", "def (a: int =)", "(a: int = 0) -> None",
                                                "(a: int = list) -> None")


def test_defaults_match_examples():
    assert defaults_match("(a: int = 1, b: int = ...)", "(a: int = 1, b: int = list)")
    assert defaults_match("(b: int = fn)", "(b: int = 7)", {"fn"})
    assert not defaults_match("(a: int = 1)", "(a: int = 2)")
    assert not defaults_match("(a: int = 1)", "(a: int)")
    assert not defaults_match("(a: int = 1, b: int = ...)", "(a: int = 2, b: int = list)")


def test_display_canon_examples():
    assert display_canon("def (float)") == display_canon("(float, /) -> None")
    assert display_canon("Foo[P.args]") != display_canon("Foo[P.kwargs]")
    # a default value with a comma inside brackets or quotes is dropped as a whole, the next parameter is kept
    assert display_canon("def (a: int =, b: str =) -> None") == display_canon("(a: int = 3, b: str = 'x') -> None")
    assert display_canon("def (a: list[int] =, b: str)") == display_canon("(a: list[int] = [1, 2], b: str) -> None")
    assert display_canon("def (a: int =, b: str)") != display_canon("(a: int, b: str) -> None")


# ------------------------------------------------------------------------------------------------ upstream kind only_pyright
def test_only_pyright_entries_do_not_fire_on_other_kinds_or_messages():
    msg = ('reportArgumentType', 'Argument of type "Plain" cannot be assigned to parameter "x" of type "Hashable"')
    assert not {i for i in pids(HASH + "need(Plain())\n", "need(Plain())", K.ONLY_MYPY, mypy=[("arg-type", msg[1])])
                if "2455" in i}
    assert not {i for i in pids(HASH + "need(Plain())\n", "need(Plain())", K.ONLY_PYRIGHT, pyright=[]) if "2455" in i}


# ------------------------------------------------------------------------------------------------ runtime evidence
CATCH = ("def f(x: int) -> int:\n    return x + 1\n\n\ntry:\n    f('a')  # expect-error\nexcept TypeError:\n    pass\n")


def test_harness_records_caught_exceptions(tmp_path: Path):
    prog, out = tmp_path / "case.py", tmp_path / "out.json"
    prog.write_text(CATCH)
    harness = Path(__file__).parent.parent / "typediff" / "runtime_harness.py"
    subprocess.run([sys.executable, str(harness), str(prog), str(out), "10"], check=True, capture_output=True)
    res = json.loads(out.read_text())
    assert res["status"] == "success"
    assert any(r[1] == "TypeError" and r[0] == 6 for r in res["raised"]), res["raised"]
    from typediff.parsers import runtime_from_json

    assert any(t == "TypeError" and ln == 6 for ln, t, _ in runtime_from_json(res).raised)


def test_handled_type_exception_makes_pyright_only_a_supports():
    am = AnchorMap(CATCH)
    caught = RuntimeResult(status="success", executed_lines=[1, 2, 5, 6, 8],
                           raised=[(2, "TypeError", 'can only concatenate str (not "int") to str'),
                                   (6, "TypeError", 'can only concatenate str (not "int") to str')])
    assert pyright_runtime_relation(am, caught, 6) == "supports"
    assert handled_type_exception(caught, 6, 6)
    plain = RuntimeResult(status="success", executed_lines=[1, 2, 5, 6, 8])
    assert pyright_runtime_relation(am, plain, 6) == "contradicts"
    # controls: raised elsewhere, a weak/none exception class, an exception that is not a type error
    elsewhere = RuntimeResult(status="success", executed_lines=[1, 2, 5, 6, 8], raised=[(2, "TypeError", "x")])
    assert pyright_runtime_relation(am, elsewhere, 6) == "contradicts"
    stop = RuntimeResult(status="success", executed_lines=[1, 2, 5, 6, 8], raised=[(6, "StopIteration", "")])
    assert pyright_runtime_relation(am, stop, 6) == "contradicts"
    zero = RuntimeResult(status="success", executed_lines=[1, 2, 5, 6, 8], raised=[(6, "ZeroDivisionError", "division by zero")])
    assert pyright_runtime_relation(am, zero, 6) == "contradicts"


def test_only_pyright_with_a_handled_exception_gets_the_higher_priority_and_says_so():
    am_src = CATCH
    pyr = Diagnostic(Tool.PYRIGHT, 6, 1, Severity.ERROR, "reportArgumentType", 'Argument of type "str" cannot be assigned')
    rt = RuntimeResult(status="success", executed_lines=[1, 2, 5, 6, 8], raised=[(6, "TypeError", "boom")])
    diags = {Tool.MYPY: [], Tool.TY: [], Tool.PYRIGHT: [pyr]}
    ds = find_discrepancies(diags, AnchorMap(am_src), rt, pyright_only=True)
    (d,) = [x for x in ds if x.kind == K.ONLY_PYRIGHT]
    assert d.reveal_relation == "runtime_supports" and d.priority == 0.7
    st = CaseState("t", am_src, "3.13", diags, rt, [], {}, {}, pyright_ran=True)
    attach_pyright_evidence(st, d)
    (ev,) = d.evidence
    assert "handled it" in ev.summary and "matches the runtime" in ev.summary
    # control: no exception recorded -> the old wording and priority
    rt2 = RuntimeResult(status="success", executed_lines=[1, 2, 5, 6, 8])
    (d2,) = [x for x in find_discrepancies(diags, AnchorMap(am_src), rt2, pyright_only=True) if x.kind == K.ONLY_PYRIGHT]
    assert d2.reveal_relation == "runtime_contradicts" and d2.priority == 0.3


# ---- runtime_miss after an `# expect-error` line
EXPECT = ("def use(x: int) -> None: ...\n"
          "def run(cb) -> None:\n"
          "    cb(1)\n"
          "hf = lambda v: v.bit_length2()\n"
          "use(hf)  # expect-error\n"
          "run(hf)\n")
# the marked statement and the failing chain share no program name: the failure is a genuine miss
UNRELATED = ("def use(x: int) -> None: ...\n"
             "def run(cb) -> None:\n"
             "    cb(1)\n"
             "use('a')  # expect-error\n"
             "run(lambda v: v.bit_length2())\n")


def miss_rt(frames, executed=(1, 2, 3, 4, 5, 6)):
    return RuntimeResult(status="exception", exc_type="AttributeError", exc_message="'int' object has no attribute 'bit_length2'",
                         exc_line=frames[-1][0], frames=frames, executed_lines=list(executed))


def miss_kinds(src, diags, rt):
    return [d.kind for d in find_discrepancies(diags, AnchorMap(src), rt)]


FRAMES = [(6, "<module>"), (3, "run"), (4, "<lambda>")]


def _flag(line, tool=Tool.MYPY, code="arg-type"):
    d = {Tool.MYPY: [], Tool.TY: [], Tool.PYRIGHT: []}
    d[tool] = [Diagnostic(tool, line, 1, Severity.ERROR, code, "bad")]
    return d


def test_runtime_miss_that_follows_a_flagged_expect_error_line_is_not_reported():
    assert K.RUNTIME_MISS not in miss_kinds(EXPECT, _flag(5), miss_rt(FRAMES))
    # any of the three checkers flagging the marker is enough
    assert K.RUNTIME_MISS not in miss_kinds(EXPECT, _flag(5, Tool.PYRIGHT, "reportArgumentType"), miss_rt(FRAMES))
    # the link can also be a function on the traceback: the marked statement calls `run`, the failure is inside it
    via_func = EXPECT.replace("use(hf)  # expect-error\nrun(hf)\n", "run(lambda v: v.bit_length2())  # expect-error\nrun(hf)\n")
    assert K.RUNTIME_MISS not in miss_kinds(via_func, _flag(5), miss_rt(FRAMES))


def test_runtime_miss_controls_stay():
    none = {Tool.MYPY: [], Tool.TY: [], Tool.PYRIGHT: []}
    assert K.RUNTIME_MISS in miss_kinds(EXPECT, none, miss_rt(FRAMES)), "marker not flagged by any checker"
    assert K.RUNTIME_MISS in miss_kinds(EXPECT.replace("  # expect-error", ""), _flag(5), miss_rt(FRAMES)), "no marker"
    assert K.RUNTIME_MISS in miss_kinds(EXPECT, _flag(5), miss_rt(FRAMES, executed=(1, 2, 3, 4, 6))), "marker never ran"
    later = EXPECT.replace("use(hf)  # expect-error\nrun(hf)\n", "run(hf)\nuse(hf)  # expect-error\n")
    assert K.RUNTIME_MISS in miss_kinds(later, _flag(6), miss_rt([(5, "<module>"), (3, "run"), (4, "<lambda>")])), \
        "the failing statement comes first"


def test_runtime_miss_after_a_flagged_marker_that_shares_nothing_with_the_failure_stays():
    # review finding: an unrelated genuine miss after a flagged `# expect-error` line must not be hidden
    frames = [(5, "<module>"), (3, "run"), (5, "<lambda>")]
    assert K.RUNTIME_MISS in miss_kinds(UNRELATED, _flag(4), miss_rt(frames, executed=(1, 2, 3, 4, 5)))
    # names that every program has (builtins, `self`) are no link
    builtin_link = UNRELATED.replace("use('a')", "print(len('a'), use('a'))").replace("cb(1)", "print(cb(1))")
    assert K.RUNTIME_MISS in miss_kinds(builtin_link, _flag(4), miss_rt(frames, executed=(1, 2, 3, 4, 5)))


def test_runtime_miss_traceback_starting_before_the_marker_stays():
    src = ("def run(cb) -> None:\n    cb(1)\n\n\nrun(lambda v: v.nope)\nuse = 1\nuse  # expect-error\n")
    flagged = {Tool.MYPY: [Diagnostic(Tool.MYPY, 7, 1, Severity.ERROR, "misc", "bad")], Tool.TY: [], Tool.PYRIGHT: []}
    rt = RuntimeResult(status="exception", exc_type="AttributeError", exc_message="x", exc_line=5,
                       frames=[(5, "<module>"), (2, "run"), (5, "<lambda>")], executed_lines=[1, 2, 5, 6, 7])
    assert K.RUNTIME_MISS in miss_kinds(src, flagged, rt)


# ---- mypy's `...` in a recursive alias is not a variadic tuple
REC = ("from typing import reveal_type\n\ntype Left = tuple[int, Right] | None\ntype Right = tuple[str, Left]\n\n"
       "sample: Left = (1, ('a', None))\nreveal_type(sample[1])\n")
PLAIN_TUPLE = "from typing import reveal_type\n\nsample: tuple[int, tuple[str, None]] = (1, ('a', None))\nreveal_type(sample[1])\n"
STR_SHAPE = {"type": "builtins.str", "mro": ["builtins.str", "builtins.object"], "repr": "'a'", "literal": "'a'"}
NONE_SHAPE = {"type": "builtins.NoneType", "mro": ["builtins.NoneType", "builtins.object"], "repr": "None"}
TUP_SHAPE = {"type": "builtins.tuple", "mro": ["builtins.tuple", "builtins.object"], "repr": "('a', None)", "len": 2,
             "items": [STR_SHAPE, NONE_SHAPE]}


def alias_case(src, mypy_rev):
    n = len(src.splitlines())
    rt = RuntimeResult(status="success", probes=[RuntimeProbe(n, TUP_SHAPE)], executed_lines=list(range(1, n + 1)))
    my = Diagnostic(Tool.MYPY, n, 1, Severity.NOTE, None, f'Revealed type is "{mypy_rev}"', revealed_type=mypy_rev)
    ty = Diagnostic(Tool.TY, n, 1, Severity.NOTE, "revealed-type", "Revealed type: `tuple[str, None]`", revealed_type="tuple[str, None]")
    st = CaseState("t", src, "3.13", {Tool.MYPY: [my], Tool.TY: [ty]}, rt, [], {}, {})
    d = find_discrepancies(st.diags, st.amap, st.runtime)[0]
    attach_runtime_evidence(st, d)
    return d


def strong_bug(d):
    return [e for e in d.evidence if e.supports == "bug" and e.strength == "strong"]


def test_recursive_alias_dots_are_not_a_variadic_tuple():
    d = alias_case(REC, "tuple[str, ...]")
    assert not strong_bug(d), d.evidence
    assert any("recursive type alias" in e.summary for e in d.evidence)


def test_dots_without_a_recursive_alias_stay_strong():
    assert strong_bug(alias_case(PLAIN_TUPLE, "tuple[builtins.int, ...]")) or strong_bug(alias_case(PLAIN_TUPLE, "tuple[int, ...]"))


def test_recursive_aliases_are_found_directly_and_through_other_aliases():
    import ast

    assert recursive_aliases(ast.parse(REC)) == {"Left", "Right"}
    assert recursive_aliases(ast.parse("type A = list[B]\ntype B = int\n")) == set()
    assert recursive_aliases(ast.parse("from typing import TypeAlias\nJ: TypeAlias = 'list[J] | int'\n")) == {"J"}
    assert recursive_aliases(ast.parse("type X = list['X']\nx = 1\n")) == {"X"}
    assert recursive_aliases(None) == set()
