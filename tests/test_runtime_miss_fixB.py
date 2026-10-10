"""runtime_miss anchoring: compound headers, ignore comments."""

from __future__ import annotations

from typediff.anchors import AnchorMap
from typediff.discrepancy import find_discrepancies
from typediff.models import Diagnostic, DiscrepancyKind as K, RuntimeResult, Severity, Tool

ENUM = "from enum import Enum\n\n\nclass Planet(Enum):\n    A = 1\n    B = (1, 2)\n"


def rt(line):
    return RuntimeResult(status="exception", exc_type="TypeError", exc_message="takes 1 positional argument but 2 were given",
                         exc_line=line, frames=[(line, "<module>")])


def kinds(src, line, diags):
    return [d.kind for d in find_discrepancies(diags, AnchorMap(src), rt(line))]


def test_enum_header_with_body_diag_not_runtime_miss():
    diags = {Tool.PYRIGHT: [Diagnostic(Tool.PYRIGHT, 6, 1, Severity.ERROR, "reportCallIssue", "missing arguments")],
             Tool.MYPY: [], Tool.TY: []}
    assert K.RUNTIME_MISS not in kinds(ENUM, 4, diags)


def test_type_ignore_not_runtime_miss():
    src = "def x(): ...\nx(1)  # type: ignore\n"
    assert K.RUNTIME_MISS not in kinds(src, 2, {Tool.MYPY: [], Tool.TY: []})


def test_plain_statement_still_runtime_miss():
    src = "def x(): ...\nx(1)\n"
    assert K.RUNTIME_MISS in kinds(src, 2, {Tool.MYPY: [], Tool.TY: []})
