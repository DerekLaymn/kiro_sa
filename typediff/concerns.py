"""Decide whether a mypy error code, a ty rule and a pyright rule talk about the *same concern*.

Primary source: ty's official rule-mapping table (vendored in data/ty_rule_map.json, regenerate
with ``typediff fetch-docs --refresh-rule-map``). Fallback: a small hand-written family table.
The mapping is only ever used to *pair* diagnostics; an unknown code never causes a dismissal.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .models import Diagnostic, Tool

DATA = Path(__file__).parent / "data" / "ty_rule_map.json"

# Hand families: coarse buckets used when the table has no row for a pair.
_FAMILY = {
    # mypy
    "arg-type": "argument", "call-arg": "call", "call-overload": "overload", "assignment": "assignment",
    "return-value": "return", "return": "return", "empty-body": "return", "attr-defined": "attribute",
    "union-attr": "attribute", "name-defined": "name", "used-before-def": "name", "possibly-undefined": "unbound",
    "index": "subscript", "operator": "operator", "override": "override", "valid-type": "type-form",
    "type-arg": "type-form", "type-var": "typevar", "assert-type": "assert-type", "redundant-cast": "cast",
    "unused-ignore": "ignore", "typeddict-item": "typeddict", "typeddict-unknown-key": "typeddict",
    "literal-required": "typeddict", "abstract": "abstract", "no-redef": "redefinition", "list-item": "assignment",
    "dict-item": "assignment", "misc": "*", "syntax": "syntax", "import-not-found": "import", "import": "import",
    "import-untyped": "import", "var-annotated": "inference", "has-type": "inference", "valid-newtype": "newtype",
    "func-returns-value": "none-usage", "exit-return": "context-manager", "await-not-async": "await",
    "unused-coroutine": "await", "unused-awaitable": "await", "truthy-bool": "truthiness",
    "truthy-function": "truthiness", "comparison-overlap": "truthiness", "redundant-expr": "truthiness",
    "unreachable": "truthiness", "method-assign": "assignment", "overload-overlap": "overload-def",
    "no-overload-impl": "overload-def", "metaclass": "class-def", "deprecated": "deprecated",
    "str-format": "format", "str-bytes-safe": "format", "exhaustive-match": "match",
    # ty
    "invalid-argument-type": "argument", "missing-argument": "call", "unknown-argument": "call",
    "too-many-positional-arguments": "call", "parameter-already-assigned": "call",
    "positional-only-parameter-as-kwarg": "call", "no-matching-overload": "overload",
    "invalid-assignment": "assignment", "invalid-return-type": "return", "unresolved-attribute": "attribute",
    "possibly-missing-attribute": "attribute", "invalid-attribute-access": "attribute",
    "unresolved-reference": "name", "possibly-unresolved-reference": "unbound", "not-subscriptable": "subscript",
    "index-out-of-bounds": "subscript", "invalid-key": "typeddict", "missing-typed-dict-key": "typeddict",
    "unsupported-operator": "operator", "unsupported-bool-conversion": "operator",
    "invalid-method-override": "override", "invalid-attribute-override": "override", "invalid-type-form": "type-form",
    "invalid-type-arguments": "type-form", "type-assertion-failure": "assert-type",
    "unused-ignore-comment": "ignore", "unused-type-ignore-comment": "ignore", "unresolved-import": "import",
    "possibly-missing-import": "import", "call-non-callable": "operator", "conflicting-declarations": "redefinition",
    "invalid-declaration": "redefinition", "invalid-overload": "overload-def", "invalid-syntax": "syntax",
    "invalid-await": "await", "redundant-condition": "truthiness",
    "invalid-context-manager": "context-manager", "not-iterable": "iteration",
    "invalid-parameter-default": "assignment", "invalid-newtype": "newtype", "call-abstract-method": "abstract",
    # pyright
    "reportArgumentType": "argument", "reportCallIssue": "call", "reportAssignmentType": "assignment",
    "reportReturnType": "return", "reportAttributeAccessIssue": "attribute", "reportOptionalMemberAccess": "attribute",
    "reportUndefinedVariable": "name", "reportPossiblyUnbound": "unbound", "reportIndexIssue": "subscript",
    "reportOptionalSubscript": "subscript", "reportOperatorIssue": "operator", "reportOptionalOperand": "operator",
    "reportIncompatibleMethodOverride": "override", "reportIncompatibleVariableOverride": "override",
    "reportInvalidTypeForm": "type-form", "reportAssertTypeFailure": "assert-type", "reportUnnecessaryCast": "cast",
    "reportMissingImports": "import", "reportGeneralTypeIssues": "*", "reportTypedDictNotRequiredAccess": "typeddict",
    "reportAbstractUsage": "abstract", "reportRedeclaration": "redefinition", "reportOptionalIterable": "iteration",
    "reportOptionalCall": "operator", "reportNoOverloadImplementation": "overload-def",
    "reportInvalidTypeVarUse": "typevar", "reportUnusedCoroutine": "await",
}


@dataclass(frozen=True)
class RuleRow:
    ty: tuple[str, ...]
    mypy: tuple[str, ...]
    pyright: tuple[str, ...]
    note: str
    issues: tuple[str, ...]
    partial: bool


@lru_cache(maxsize=1)
def rule_rows() -> tuple[RuleRow, ...]:
    if not DATA.exists():
        return ()
    doc = json.loads(DATA.read_text())
    return tuple(
        RuleRow(tuple(r["ty"]), tuple(r["mypy"]), tuple(r["pyright"]), r.get("note", ""), tuple(r.get("ty_issues", [])),
                bool(r.get("partial")))
        for r in doc.get("rows", [])
    )


def family(code: str | None) -> str | None:
    return _FAMILY.get(code or "")


def same_concern(a: Diagnostic, b: Diagnostic) -> bool:
    """True if two problem diagnostics from different tools plausibly describe the same issue."""
    if a.tool == b.tool:
        return a.code == b.code
    ca, cb = a.code or "", b.code or ""
    pair = {a.tool: ca, b.tool: cb}
    for row in rule_rows():
        if Tool.TY in pair and Tool.MYPY in pair and pair[Tool.TY] in row.ty and pair[Tool.MYPY] in row.mypy:
            return True
        if Tool.TY in pair and Tool.PYRIGHT in pair and pair[Tool.TY] in row.ty and pair[Tool.PYRIGHT] in row.pyright:
            return True
        if Tool.MYPY in pair and Tool.PYRIGHT in pair and pair[Tool.MYPY] in row.mypy and pair[Tool.PYRIGHT] in row.pyright:
            return True
    fa, fb = family(ca), family(cb)
    if fa and fb and (fa == fb or "*" in (fa, fb)):
        return True
    return False


def mypy_checks_without_ty_equivalent() -> dict[str, RuleRow]:
    """mypy codes that ty documents as not implemented ("None yet", "No direct equivalent planned").

    A code that ALSO appears in a row that has a ty rule (e.g. ``attr-defined``: implemented, except for
    non-re-exported names) is only *partially* missing; it is returned with ``partial=True`` so it can
    never trigger an automatic KNOWN_LIMITATION dismissal.
    """
    with_ty = {c for row in rule_rows() if row.ty for c in row.mypy}
    out: dict[str, RuleRow] = {}
    for row in rule_rows():
        if row.ty:
            continue
        for code in row.mypy:
            entry = row
            if code in with_ty and not row.partial:
                entry = RuleRow(row.ty, row.mypy, row.pyright, row.note, row.issues, True)
            out.setdefault(code, entry)
    return out


def ty_rules_without_mypy_equivalent() -> set[str]:
    with_mypy = {r for row in rule_rows() if row.mypy for r in row.ty}
    only = {r for row in rule_rows() if row.ty and not row.mypy for r in row.ty}
    return only - with_mypy


def mypy_codes_for_ty_rule(rule: str) -> set[str]:
    return {c for row in rule_rows() if rule in row.ty for c in row.mypy}


# mypy error codes that are disabled unless explicitly enabled (mypy docs: error_code_list2.rst)
MYPY_OPTIONAL_CODES = {
    "redundant-self", "redundant-expr", "possibly-undefined", "truthy-bool", "truthy-iterable", "ignore-without-code",
    "unused-awaitable", "unused-ignore", "explicit-override", "mutable-override", "unimported-reveal", "deprecated",
    "exhaustive-match", "untyped-decorator", "no-untyped-def", "no-untyped-call", "no-any-return", "unreachable",
    "comparison-overlap", "redundant-cast", "explicit-any", "narrowed-type-not-subtype",
}
