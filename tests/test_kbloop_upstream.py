"""kb-loop round 1: UPSTREAM-MYPY-948 (unquoted forward references), positive and negative examples."""

from __future__ import annotations

from typediff.kb import matching_entries
from typediff.models import Diagnostic, Discrepancy, DiscrepancyKind as K, RuntimeResult, Severity, Tool
from typediff.state import CaseState


def dg(tool, line, code, msg):
    return Diagnostic(tool, line, 1, Severity.ERROR, code, msg)


def case(src, line, name="A", pyright=True, ty_name=None):
    t = dg(Tool.TY, line, "unresolved-reference", f"Name `{ty_name or name}` used when not defined")
    p = [dg(Tool.PYRIGHT, line, "reportUndefinedVariable", f'"{name}" is not defined')] if pyright else []
    st = CaseState("t", src, "3.13", {Tool.MYPY: [], Tool.TY: [t], Tool.PYRIGHT: p}, RuntimeResult(status="success"),
                   [], {}, {}, pyright_ran=True)
    return st, Discrepancy("D1", K.ONLY_TY, line, line, "s", "", ty=[t], pyright=p)


def hit(st, d):
    return "UPSTREAM-MYPY-948" in {e.id for e in matching_entries(st, d)}


def test_self_reference_in_class_body():
    assert hit(*case("class A:\n    def f(self, o: A) -> None: ...\n", 2))


def test_class_defined_later():
    assert hit(*case("def f(x: B) -> None: ...\n\n\nclass B: ...\n", 1, name="B"))


def test_variable_annotation_forward_reference():
    assert hit(*case("x: B\n\n\nclass B: ...\n", 1, name="B"))


# ---------------------------------------------------------------- negatives


def test_future_import_means_ty_is_wrong_not_mypy():
    assert not hit(*case("from __future__ import annotations\n\n\nclass A:\n    def f(self, o: A) -> None: ...\n", 5))


def test_truly_undefined_name_not_matched():
    assert not hit(*case("def f(x: Nope) -> None: ...\n", 1, name="Nope"))


def test_quoted_reference_is_not_a_forward_reference_problem():
    assert not hit(*case("class A:\n    def f(self, o: 'A') -> None: ...\n", 2))


def test_name_used_outside_annotation_not_matched():
    assert not hit(*case("x = B()\n\n\nclass B: ...\n", 1, name="B"))


def test_pyright_must_agree():
    assert not hit(*case("class A:\n    def f(self, o: A) -> None: ...\n", 2, pyright=False))


def test_other_undefined_name_in_same_statement_not_matched():
    st, d = case("class A:\n    def f(self, o: A, p: Nope) -> None: ...\n", 2)
    extra = dg(Tool.TY, 2, "unresolved-reference", "Name `Nope` used when not defined")
    d.ty.append(extra)
    assert not hit(st, d)
