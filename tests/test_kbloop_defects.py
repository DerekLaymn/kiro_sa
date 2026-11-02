"""Regression tests for pipeline defects found while triaging kb-loop round 1 (false 'strong' runtime evidence)."""

from __future__ import annotations

from typediff.experiments import default_probe_exprs
from typediff.inhabit import inhabits
from typediff.models import Discrepancy, DiscrepancyKind as K, RuntimeResult, Tool
from typediff.rules import _stub_callee
from typediff.state import CaseState
from typediff.typenorm import normalize


def st(src):
    return CaseState("t", src, "3.13", {Tool.MYPY: [], Tool.TY: []}, RuntimeResult(status="success"), [], {}, {})


def tup(*item_types):
    return {"type": "builtins.tuple", "mro": ["builtins.tuple", "builtins.object"], "len": len(item_types),
            "items": [{"type": f"builtins.{t}", "mro": [f"builtins.{t}", "builtins.object"], "repr": "x"} for t in item_types]}


# D1: variadic tuple types were matched positionally, so a 4-tuple "did not inhabit" tuple[A, *tuple[B, ...], C]
def test_variadic_tuple_is_undecided_not_false():
    t = normalize("tuple[int, *tuple[int, ...], int]", "case")
    assert inhabits(tup("int", "int", "int", "int"), t) is None
    t2 = normalize("tuple[int, Unpack[tuple[int, ...]], int]", "case")
    assert inhabits(tup("int", "int", "int", "int"), t2) is None


def test_plain_tuple_arity_mismatch_still_false():  # negative: the definite answers stay
    assert inhabits(tup("int", "int", "int", "int"), normalize("tuple[int, int, int]", "case")) is False


# D2: typing aliases / special forms (Hashable, Mapping, C[int]) stand for classes at runtime
def test_special_generic_alias_is_undecided_for_type_of():
    shape = {"type": "typing._SpecialGenericAlias", "mro": ["typing._SpecialGenericAlias", "builtins.object"]}
    assert inhabits(shape, normalize("type[Hashable]", "case")) is None


def test_plain_instance_still_outside_type_of():  # negative
    shape = {"type": "builtins.int", "mro": ["builtins.int", "builtins.object"], "repr": "1"}
    assert inhabits(shape, normalize("type[int]", "case"), {"int"}) is False


# D3: operators and subscripts call stub-bodied dunder methods whose runtime value is None
def test_stub_dunder_operator_is_recognised():
    s = st("class A:\n    def __add__(self, o: 'A') -> str: ...\n\n\nx = A() + A()\n")
    assert _stub_callee(s, 5) == "__add__"
    s = st("class A:\n    def __getitem__(self, i: int) -> int:\n        pass\n\n\nx = A()[0]\n")
    assert _stub_callee(s, 6) == "__getitem__"


def test_real_dunder_body_is_not_a_stub():  # negative
    s = st("class A:\n    def __add__(self, o: 'A') -> str:\n        return 'x'\n\n\nx = A() + A()\n")
    assert _stub_callee(s, 6) is None
    s = st("class A:\n    def __add__(self, o: 'A') -> None: ...\n\n\nx = A() + A()\n")  # annotated -> None: not a stub
    assert _stub_callee(s, 5) is None


# D4: a subclass of a TypedDict is a dict at runtime, not a nominal class
def test_typeddict_subclass_is_not_nominal():
    s = st("from typing import TypedDict\n\n\nclass A(TypedDict):\n    a: int\n\n\nclass B(A):\n    b: int\n\n\nclass C: ...\n")
    assert "B" not in s.nominal_classes and "A" not in s.nominal_classes
    assert "C" in s.nominal_classes  # negative


# D5: TYPE_CHECKING is False at runtime and True for checkers by definition
def test_type_checking_is_not_probed():
    s = st("from typing import TYPE_CHECKING\nimport typing\n\nif TYPE_CHECKING and typing.TYPE_CHECKING and flag:\n    pass\n")
    d = Discrepancy("D1", K.ONLY_MYPY, 4, 5, "if", "")
    exprs = default_probe_exprs(s, d)
    assert "TYPE_CHECKING" not in exprs and "typing.TYPE_CHECKING" not in exprs and "flag" in exprs
