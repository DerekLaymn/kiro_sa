"""Curated knowledge base of *documented* mypy/ty behaviour differences.

Each entry is an auditable, citable reason a discrepancy may NOT be a bug. Three levels of trust:

* ``auto=False``          hint only - shown to the LLM, never dismisses anything by itself
* ``auto=True``           may dismiss deterministically when the (precise) matcher fires
* ``auto=True, verify=``  may dismiss only after a deterministic experiment confirms it
                          (e.g. the discrepancy disappears under the documented config toggle)

``runtime_override=True`` means: if CPython contradicts the entry's implied safety claim at this
statement (type-related exception / probe value outside the more precise type), the entry is
demoted to a hint and the case goes to adjudication. That single switch is what keeps the KB
from swallowing genuine soundness bugs that *look like* a known divergence.

Entries were calibrated against ty 0.0.84 / mypy 2.4.0 (2026-10). Re-validate after upgrades:
``typediff kb-selftest`` re-runs every entry's canonical example.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .concerns import (
    MYPY_OPTIONAL_CODES, mypy_checks_without_ty_equivalent, mypy_codes_for_ty_rule, rule_rows,
    ty_rules_without_mypy_equivalent,
)
from .discrepancy import META_CODES
from .experiments import MYPY_CODE_ENABLERS, ExperimentRunner
from .inhabit import inhabits
from .models import Discrepancy, DiscrepancyKind, Dismissal, Evidence, EvidenceType, Tool
from .parsers import classify_exception
from .state import CaseState
from .typenorm import gradual_diff, is_join_vs_union, is_literal_widening, normalize

K = DiscrepancyKind
TY_DOCS = "https://docs.astral.sh/ty"


@dataclass
class KBEntry:
    id: str
    title: str
    dismissal: Dismissal
    source: str
    text: str
    kinds: tuple[DiscrepancyKind, ...]
    matcher: Callable[[CaseState, Discrepancy], bool]
    auto: bool = False
    runtime_override: bool = True
    runtime_override_kinds: tuple[DiscrepancyKind, ...] = ()  # kinds for which a runtime contradiction demotes the entry anyway
    verify: Callable[[CaseState, Discrepancy, ExperimentRunner], Evidence | None] | None = None
    example: str = ""  # canonical program for kb-selftest

    def prompt_text(self) -> str:
        return f"[KB:{self.id}] {self.title} (dismissal={self.dismissal.value}; source: {self.source})\n{self.text}"


# --------------------------------------------------------------------------- matcher helpers


def _stmt_node(s: CaseState, d: Discrepancy) -> ast.AST | None:
    st = s.amap.stmt(d.anchor)
    return st.node if st else None


def _chain_tags(s: CaseState, d: Discrepancy) -> set[str]:
    from .features import tags_for_nodes

    chain = s.amap.enclosing_nodes(d.anchor)
    tags: set[str] = set()
    for n in chain:
        if isinstance(n, (ast.If, ast.While)):
            tags |= tags_for_nodes([n.test])
        elif isinstance(n, ast.match_case):
            tags.add("match_case")
            if any(isinstance(p, (ast.MatchValue,)) for p in ast.walk(n.pattern)):
                tags.add("match_value")
            if any(isinstance(p, ast.MatchClass) for p in ast.walk(n.pattern)):
                tags.add("match_class")
        elif isinstance(n, ast.Assert):
            tags |= tags_for_nodes([n.test])
    node = _stmt_node(s, d)
    if isinstance(node, (ast.If, ast.While, ast.Assert)):
        tags |= tags_for_nodes([node.test])
    return tags


def _codes(diags) -> set[str]:
    return {x.code or "" for x in diags}


def _rev(d: Discrepancy, tool: str, s: CaseState):
    lst = d.mypy if tool == "mypy" else d.ty
    return normalize(lst[0].revealed_type, s.module) if lst and lst[0].revealed_type is not None else None


def runtime_contradiction(s: CaseState, d: Discrepancy) -> str | None:
    """Return a description if CPython contradicts 'everything is fine here'."""
    rt = s.runtime
    if rt.status == "exception" and classify_exception(rt.exc_type, rt.exc_message) == "strong":
        frame_anchors = {s.amap.anchor(ln) for ln, _ in rt.frames}
        if d.anchor in frame_anchors:
            return f"CPython raised {rt.exc_type}: {rt.exc_message} in this statement"
    if d.kind == K.REVEAL_MISMATCH:
        for tool in ("mypy", "ty"):
            p = matched_probe(s, d, tool)  # None when the pairing is ambiguous -> never blocks a dismissal
            t = _rev(d, tool, s)
            if p is not None and t is not None and inhabits(p.shape, t, s.nominal_classes) is False:
                return f"runtime value {p.shape.get('repr')!r} ({p.shape.get('type')}) is outside {tool}'s type {t.text}"
    return None


def matched_probe(s: CaseState, d: Discrepancy, tool: str):
    """The runtime probe that belongs to this discrepancy's reveal_type call, or None if that is not certain.

    The k-th reveal of ``tool`` in the statement is paired with the k-th runtime probe of the statement. Any
    doubt (probe count differs from the reveal count because of loops / repeated calls / unexecuted branches,
    or nested reveal_type calls whose evaluation order differs from their source order) gives None."""
    mine = (d.mypy if tool == "mypy" else d.ty)
    if not mine or mine[0].revealed_type is None:
        return None
    reveals = sorted((x for x in s.diags.get(Tool(tool), []) if x.revealed_type is not None
                      and s.amap.anchor(x.line) == d.anchor), key=lambda x: (x.line, x.col or 0))
    probes = [p for p in s.runtime.probes if s.amap.anchor(p.line) == d.anchor]
    if not probes or len(probes) != len(reveals):
        return None
    node = _stmt_node(s, d)
    if node is not None:
        calls = [c for c in ast.walk(node) if isinstance(c, ast.Call)
                 and getattr(c.func, "id", getattr(c.func, "attr", None)) == "reveal_type"]
        if any(o is not c and any(i is c for i in ast.walk(o)) for o in calls for c in calls):
            return None
    try:
        k = reveals.index(mine[0])
    except ValueError:
        return None
    return probes[k]


def _toggle(tool: Tool, flags: list[str]):
    def verify(s: CaseState, d: Discrepancy, ex: ExperimentRunner) -> Evidence | None:
        if not s.online:
            return None
        r = ex.run(d, {"kind": "config_toggle", "tool": tool.value, "flags": flags})
        if not r.ok:
            return None
        if r.outcome.get("persists") is False:
            return Evidence(EvidenceType.EXPERIMENT, "not_bug",
                            f"discrepancy disappears with {tool.value} {' '.join(flags)} ({r.id})", citation=r.id,
                            verified=True, strength="strong")
        return Evidence(EvidenceType.EXPERIMENT, "neutral",
                        f"discrepancy persists with {tool.value} {' '.join(flags)} ({r.id}) - KB explanation does not apply",
                        citation=r.id, verified=True, strength="medium")
    return verify


# --------------------------------------------------------------------------- matchers


def m_redeclaration(s, d):
    """Only the documented feature: re-*annotating* a name that already has a declared type in the same
    scope (parameter or earlier annotation). Redefined functions/classes are NOT covered - mypy [no-redef]
    on decorated/conditional defs (e.g. property-subclass setters, python/mypy#6158) can be real bugs."""
    node = _stmt_node(s, d)
    if "no-redef" not in _codes(d.mypy) or not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Name):
        return False
    name = node.target.id
    chain = s.amap.enclosing_nodes(d.anchor)
    scope = next((n for n in reversed(chain[:-1]) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))), None)
    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
        a = scope.args
        if any(p.arg == name for p in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg] if p is not None):
            return True
    body = scope.body if scope is not None else (s.amap.tree.body if s.amap.tree else [])
    return any(isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == name
               and n.lineno < node.lineno for n in ast.walk(ast.Module(body=body, type_ignores=[])))


_DUNDER = re.compile(r"has no attribute `(__name__|__qualname__|__module__|__doc__|__defaults__|__code__)`")


def m_callable_dunder(s, d):
    return any(x.code == "unresolved-attribute" and _DUNDER.search(x.message) and ("->" in x.message or "Callable" in x.message)
               for x in d.ty)


def m_equality_narrowing(s, d):
    return bool(_chain_tags(s, d) & {"eq_narrow", "in_narrow", "match_value"})


def m_generic_narrowing(s, d):
    return bool(_chain_tags(s, d) & {"isinstance", "match_class", "typeis"})


def m_unknown_union(s, d):
    t, m = _rev(d, "ty", s), _rev(d, "mypy", s)
    if not (t and m and t.node and t.node.kind == "union"):
        return False
    rest = [a for a in t.node.args if a.render() != "Unknown"]
    return len(rest) < len(t.node.args) and {a.render() for a in rest} <= {x.render() for x in (m.node.args if m.node and m.node.kind == "union" else [m.node] if m.node else [])}


def m_todo(s, d):
    return d.reveal_relation == "todo" or any("@Todo" in (x.message or "") for x in d.ty)


# mypy codes ty lacks AND whose mypy-side behaviour is itself documented mypy design/config, so the
# discrepancy is fully explained. For the other missing checks (overload-overlap, type-abstract, safe-super,
# str-format, ...) the entry only exonerates ty's silence; mypy's diagnostic may still be a false positive
# (e.g. python/mypy#6140, an overload-overlap FP) and must be adjudicated.
_MYPY_DESIGN_ONLY_CODES = {"var-annotated", "import-untyped", "no-untyped-def", "no-untyped-call", "explicit-any",
                           "no-any-unimported"}


def m_ty_check_missing(s, d):
    missing = mypy_checks_without_ty_equivalent()
    codes = _codes(d.mypy)
    return bool(codes) and all(c in missing and not missing[c].partial and c in _MYPY_DESIGN_ONLY_CODES for c in codes)


def m_ty_check_missing_other(s, d):
    missing = mypy_checks_without_ty_equivalent()
    codes = _codes(d.mypy)
    return bool(codes) and all(c in missing for c in codes) and not m_ty_check_missing(s, d)


def m_ty_check_missing_partial(s, d):
    missing = mypy_checks_without_ty_equivalent()
    return any(c in missing and missing[c].partial for c in _codes(d.mypy))


def _optional_mypy_codes_for(d) -> list[str]:
    out = []
    for x in d.ty:
        codes = mypy_codes_for_ty_rule(x.code or "")
        if codes and codes <= MYPY_OPTIONAL_CODES:
            out.extend(sorted(codes))
    return sorted(set(out))


def m_mypy_optional(s, d):
    return bool(_optional_mypy_codes_for(d)) and all(mypy_codes_for_ty_rule(x.code or "") <= MYPY_OPTIONAL_CODES for x in d.ty)


def v_mypy_optional(s, d, ex):
    flags: list[str] = []
    for c in _optional_mypy_codes_for(d):
        flags += MYPY_CODE_ENABLERS.get(c, ["--enable-error-code", c])
    return _toggle(Tool.MYPY, flags)(s, d, ex) if flags else None


def m_ty_only_rule(s, d):
    only = ty_rules_without_mypy_equivalent()
    return any((x.code or "") in only for x in d.ty)


def m_untyped_defs(s, d):
    if s.mypy_checked_untyped_defs() is True:
        return False
    scope_fn = d.scope.split(".")[-1]
    note = any(x.code == "annotation-unchecked" for x in s.diags.get(Tool.MYPY, []))
    return scope_fn in s.unannotated_functions and (note or s.mypy_checked_untyped_defs() is False)


def _explicit_any_in_source(s) -> bool:
    return bool(s.amap.tree) and any(
        (isinstance(n, ast.Name) and n.id == "Any") or (isinstance(n, ast.Attribute) and n.attr == "Any")
        for n in ast.walk(s.amap.tree))


def m_both_gradual(s, d):
    """Every difference is gradual-vs-gradual (mypy Any vs ty Unknown at the same position).

    ty documents `Unknown` as the *implicit* Any: if the program spells `Any` explicitly and ty answers
    `Unknown` where mypy answers `Any`, ty may have lost the provenance of an explicit Any (a tracked bug
    class, e.g. astral-sh/ty#4536), so that case must NOT auto-dismiss."""
    t, m = _rev(d, "ty", s), _rev(d, "mypy", s)
    if not (t and m and t.node and m.node) or gradual_diff(m.node, t.node) != "both":
        return False
    if _explicit_any_in_source(s) and "Unknown" in t.text and "Any" not in t.text:
        return False
    return True


def m_literal_widening(s, d):
    t, m = _rev(d, "ty", s), _rev(d, "mypy", s)
    return bool(t and m and (is_literal_widening(t, m) or is_literal_widening(m, t)))


def m_join_union(s, d):
    t, m = _rev(d, "ty", s), _rev(d, "mypy", s)
    return bool(t and m and is_join_vs_union(m, t, _typevars(s)))


def _typevars(s) -> set[str]:
    from .experiments import _typevar_names

    return _typevar_names(s.amap.tree) if s.amap.tree else set()


_SPEC_NARROWING = {"isinstance", "typeis", "typeguard", "match_class", "match_case", "is_narrow", "hasattr",
                   "callable_narrow", "len", "in_narrow", "eq_narrow"}


def m_precision_runtime_consistent(s, d):
    if d.reveal_relation not in ("ty_more_precise", "mypy_more_precise"):
        return False
    if _chain_tags(s, d) & _SPEC_NARROWING:
        return False  # narrowing results are (partly) specified -> let the adjudicator look
    precise = _rev(d, "ty" if d.reveal_relation == "ty_more_precise" else "mypy", s)
    probes = [p for p in s.runtime.probes if s.amap.anchor(p.line) == d.anchor]
    return bool(probes) and all(inhabits(p.shape, precise, s.nominal_classes) is True for p in probes)


def m_mypy_skips_unreachable(s, d):
    if d.kind != K.REVEAL_UNPAIRED or d.mypy or not d.ty:
        return False
    rt = s.runtime
    return rt.coverage_known and d.ty[0].line not in (rt.executed_lines or [])


def m_unreachable_but_executed(s, d):
    if d.kind != K.REVEAL_UNPAIRED:
        return False
    rt = s.runtime
    line = (d.ty or d.mypy)[0].line
    return rt.coverage_known and line in (rt.executed_lines or [])


_IMPORT_CODES = {"import-not-found", "import-untyped", "import", "unresolved-import", "possibly-missing-import",
                 "reportMissingImports", "reportMissingModuleSource"}


def m_env_import(s, d):
    codes = _codes(d.mypy) | _codes(d.ty)
    return bool(codes) and codes <= _IMPORT_CODES


_IGNORE = re.compile(r"#\s*type:\s*ignore(?:\[(?P<codes>[^\]]*)\])?")


def m_suppression_expected(s, d):
    lo, hi = d.anchor, d.anchor_end
    text = "\n".join(s.amap.lines[lo - 1:hi])
    mm = _IGNORE.search(text)
    if not mm or mm["codes"] is None:
        return False
    codes = [c.strip() for c in mm["codes"].split(",") if c.strip()]
    ty_codes = {c[3:] for c in codes if c.startswith("ty:")}
    mypy_codes = {c for c in codes if ":" not in c}
    if d.kind == K.ONLY_TY:  # documented: codes without the `ty:` prefix are ignored by ty
        return all((x.code or "") not in ty_codes for x in d.ty)
    if d.kind == K.ONLY_MYPY:  # mypy only honours its own codes
        return all((x.code or "") not in mypy_codes for x in d.mypy)
    return False


def m_on_ignore_line(s, d):
    text = "\n".join(s.amap.lines[d.anchor - 1:d.anchor_end])
    return bool(re.search(r"#\s*(type|ty):\s*ignore", text))


def m_inference_downstream(s, d):
    """ONLY_* explained by different *inferred* types of an unannotated local (probe-confirmed)."""
    probe = s.probe_cache.get(d.id)
    if not probe:
        return False
    annotated = {n.target.id for n in ast.walk(s.amap.tree) if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)} if s.amap.tree else set()
    params = {a.arg for n in ast.walk(s.amap.tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
              for a in [*n.args.posonlyargs, *n.args.args, *n.args.kwonlyargs] if a.annotation is not None} if s.amap.tree else set()
    for expr, o in probe.items():
        if "." in expr or expr in annotated or expr in params:
            continue
        m, t = normalize(o.get("mypy"), s.module), normalize(o.get("ty"), s.module)
        if not (m and t):
            continue
        # direction matters: an error caused by the MORE precise inference (ty's union, ty's literal) is design;
        # a mypy false positive caused by mypy's join is a tracked mypy bug class (topic-join-v-union) -> adjudicate
        if is_join_vs_union(m, t, _typevars(s)) and d.kind == K.ONLY_TY:
            return True
        if is_literal_widening(t, m) or is_literal_widening(m, t):
            return True
    return False


def m_gradual_operand(s, d):
    probe = s.probe_cache.get(d.id) or {}
    return any("Unknown" in str(o.get("ty")) or "Any" in str(o.get("mypy")) or "@Todo" in str(o.get("ty"))
               for o in probe.values())


def m_cascade(s, d):
    node = _stmt_node(s, d)
    if node is None:
        return False
    used = {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    tool_diags = s.diags.get(Tool.MYPY if d.kind == K.ONLY_MYPY else Tool.TY, [])
    for x in tool_diags:
        if not x.is_problem or s.amap.anchor(x.line) >= d.anchor:
            continue
        st = s.amap.stmt(x.line)
        if st and st.node is not None:
            bound = {n.id for n in ast.walk(st.node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
            bound |= {st.node.name} if hasattr(st.node, "name") and isinstance(getattr(st.node, "name"), str) else set()
            if bound & used:
                return True
    return False


def m_stdlib_call(s, d):
    msgs = " ".join(x.message for x in d.mypy + d.ty)
    return bool(re.search(r'"(?:[a-z_]+\.)+[A-Za-z_]+"|`(?:[a-z_]+\.)+[A-Za-z_]+`|builtins|typeshed|overload', msgs))


def m_partial_types(s, d):
    if s.amap.tree is None:
        return False
    node = _stmt_node(s, d)
    names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)} if node else set()
    for n in ast.walk(s.amap.tree):
        if isinstance(n, ast.Assign) and isinstance(n.value, (ast.List, ast.Dict, ast.Set, ast.Constant)):
            if isinstance(n.value, ast.Constant) and n.value.value is not None:
                continue
            if isinstance(n.value, (ast.List, ast.Dict, ast.Set)) and (getattr(n.value, "elts", None) or getattr(n.value, "keys", None)):
                continue
            if any(isinstance(t, ast.Name) and t.id in names for t in n.targets):
                return True
    return False


# --------------------------------------------------------------------------- entries

ENTRIES: list[KBEntry] = [
    KBEntry(
        "TY-REDECLARATION", "ty allows redeclaring a symbol with a different type", Dismissal.DESIGN_DIVERGENCE,
        f"{TY_DOCS}/features/type-system/#redeclarations",
        "ty deliberately accepts re-annotating an existing name (even a parameter) with a new type, e.g. "
        "`def f(paths: str): paths: list[str] = paths.split(':')`. mypy reports [no-redef]. Intentional ty design for "
        "adoption, documented as a headline feature.",
        (K.ONLY_MYPY,), m_redeclaration, auto=True,
        example="def f(paths: str) -> list[str]:\n    paths: list[str] = paths.split(':')\n    return paths\n",
    ),
    KBEntry(
        "TY-CALLABLE-DUNDER", "ty rejects __name__/__qualname__/... on Callable-typed values", Dismissal.DESIGN_DIVERGENCE,
        f"{TY_DOCS}/reference/typing-faq/#why-does-ty-say-callable-has-no-attribute-__name__",
        "Not every callable has function attributes (callable class instances do not), so ty reports "
        "[unresolved-attribute] for `c.__name__` when `c: Callable[...]`. mypy accepts it. Documented ty FAQ; ty is the "
        "stricter (arguably more correct) side. Report-worthy only if ty errors on a value it knows is a function.",
        (K.ONLY_TY,), m_callable_dunder, auto=True,
        example="from typing import Callable\ndef g(c: Callable[[int], str]) -> str:\n    return c.__name__\n",
    ),
    KBEntry(
        "TY-STRICT-EQUALITY", "ty narrows on ==/!=/in/match-value by default (documented unsound)", Dismissal.DESIGN_DIVERGENCE,
        f"{TY_DOCS}/reference/configuration/#strict-equality-semantics",
        "By default ty narrows e.g. `x: str` to `Literal['a']` after `x == 'a'`, and unions after `==`/`in`/match value "
        "patterns, assuming subclasses do not override __eq__. This is knowingly unsound and is disabled by "
        "`analysis.strict-equality-semantics = true`. Verified by re-running ty with that toggle.",
        (K.ONLY_MYPY, K.REVEAL_MISMATCH, K.ONLY_TY), m_equality_narrowing, auto=True, runtime_override=False,
        verify=_toggle(Tool.TY, ["--config", "analysis.strict-equality-semantics=true"]),
        example='from typing import Literal\ndef parse(v: str) -> Literal["a"] | None:\n    if v == "a":\n        return v\n    return None\n',
    ),
    KBEntry(
        "TY-GRADUAL-GENERIC-NARROWING", "ty narrows isinstance(x, list) to list[Unknown] by default", Dismissal.DESIGN_DIVERGENCE,
        f"{TY_DOCS}/reference/configuration/#strict-generic-narrowing",
        "With `strict-generic-narrowing = false` (default) ty narrows to an unspecialised generic with gradual (Unknown) "
        "arguments, preserving compatible arguments where possible; with `true` it uses the top materialisation "
        "`Top[list[Unknown]]`. Differences that vanish under the toggle are design, not bugs.",
        (K.ONLY_MYPY, K.ONLY_TY, K.REVEAL_MISMATCH), m_generic_narrowing, auto=True, runtime_override=False,
        verify=_toggle(Tool.TY, ["--config", "analysis.strict-generic-narrowing=true"]),
    ),
    KBEntry(
        "TY-UNKNOWN-UNION", "ty unions inferred types with Unknown for unannotated declarations", Dismissal.DESIGN_DIVERGENCE,
        f"{TY_DOCS}/reference/typing-faq/#what-is-the-unknown-type-and-when-does-it-appear",
        "For unannotated attributes/variables ty infers `Unknown | <inferred>` (e.g. `Unknown | None` for "
        "`data = None` in a class body) to avoid false positives in untyped code. mypy infers the bare type.",
        (K.REVEAL_MISMATCH,), m_unknown_union, auto=True, runtime_override=True,
    ),
    KBEntry(
        "TY-TODO", "ty @Todo type: known unimplemented feature", Dismissal.KNOWN_LIMITATION,
        f"{TY_DOCS}/reference/typing-faq/#what-is-the-todo-type-and-when-does-it-appear",
        "`@Todo` marks a feature ty does not implement yet (dynamic like Any). Check the type-system tracking issue "
        "https://github.com/astral-sh/ty/issues/1889 before reporting; normally logged, not filed.",
        (K.REVEAL_MISMATCH, K.ONLY_MYPY, K.ONLY_TY), m_todo, auto=True, runtime_override=False,
        # ty is silent-or-@Todo there: if CPython raised a type exception at the statement, mypy would be a false negative
        runtime_override_kinds=(K.ONLY_TY,),
    ),
    KBEntry(
        "TY-CHECK-NOT-IMPLEMENTED", "mypy-only check that ty does not implement, documented mypy behaviour",
        Dismissal.KNOWN_LIMITATION, "https://github.com/astral-sh/ty/blob/main/docs/coming-from-mypy-or-pyright.md#rules",
        "ty's official rule-mapping table lists this mypy error code with no ty equivalent, and the mypy side is "
        "documented mypy design/configuration (e.g. [var-annotated]: mypy requires annotations for empty collections; "
        "ty infers `list[Unknown]`). Both behaviours are intended.",
        (K.ONLY_MYPY,), m_ty_check_missing, auto=True, runtime_override=False,
    ),
    KBEntry(
        "TY-CHECK-MISSING-JUDGE-MYPY", "ty lacks this mypy check - only mypy's diagnostic is in question",
        Dismissal.KNOWN_LIMITATION, "https://github.com/astral-sh/ty/blob/main/docs/coming-from-mypy-or-pyright.md#rules",
        "HINT: ty documents no equivalent for this mypy code ('None yet'), so ty's silence is expected and NOT a ty "
        "bug. The remaining question is whether mypy's diagnostic is correct: if the code is spec-valid this is a "
        "mypy FALSE_POSITIVE (e.g. overload-overlap false positives are tracked mypy bugs).",
        (K.ONLY_MYPY,), m_ty_check_missing_other,
    ),
    KBEntry(
        "TY-CHECK-PARTIAL", "mypy check that ty implements only partially", Dismissal.KNOWN_LIMITATION,
        "https://github.com/astral-sh/ty/blob/main/docs/coming-from-mypy-or-pyright.md#rules",
        "The mapping table says ty covers only some cases of this mypy code ('None yet for other cases'). The concrete "
        "case may or may not be covered - decide from the tracking issue / spec.",
        (K.ONLY_MYPY,), m_ty_check_missing_partial,
    ),
    KBEntry(
        "MYPY-OPTIONAL-CHECK", "ty rule whose mypy counterpart is disabled by default", Dismissal.CONFIG_ARTIFACT,
        "https://mypy.readthedocs.io/en/stable/error_code_list2.html",
        "The ty rule maps to mypy error codes that mypy only emits when explicitly enabled. Verified by re-running mypy "
        "with the code enabled.",
        (K.ONLY_TY,), m_mypy_optional, auto=True, verify=v_mypy_optional,
    ),
    KBEntry(
        "TY-ONLY-CHECK", "ty implements a check that mypy does not have", Dismissal.DESIGN_DIVERGENCE,
        "https://github.com/astral-sh/ty/blob/main/docs/coming-from-mypy-or-pyright.md#rules",
        "This ty rule has no mypy equivalent in the official mapping. mypy's silence is expected; ty can still be WRONG "
        "(false positive) - judge ty's claim on its merits (runtime, spec).",
        (K.ONLY_TY,), m_ty_only_rule,
    ),
    KBEntry(
        "MYPY-UNTYPED-DEFS", "mypy skips bodies of unannotated functions without --check-untyped-defs", Dismissal.CONFIG_ARTIFACT,
        "https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-check-untyped-defs",
        "ty always checks unannotated function bodies; mypy only with --check-untyped-defs (it emits an "
        "[annotation-unchecked] note). Discrepancies inside such functions are configuration artefacts.",
        (K.ONLY_TY, K.REVEAL_MISMATCH), m_untyped_defs, auto=True, runtime_override=False,
    ),
    KBEntry(
        "BOTH-GRADUAL", "both checkers fall back to a gradual type", Dismissal.SPEC_AMBIGUITY,
        "https://typing.python.org/en/latest/spec/concepts.html",
        "mypy reveals Any and ty reveals Unknown/Any (possibly with different surrounding structure). How much structure "
        "is preserved around a gradual type is implementation-defined.",
        (K.REVEAL_MISMATCH,), m_both_gradual, auto=True, runtime_override=False,
    ),
    KBEntry(
        "LITERAL-WIDENING", "ty keeps Literal types where mypy widens", Dismissal.DESIGN_DIVERGENCE,
        "https://typing.python.org/en/latest/spec/literal.html",
        "For inferred (unannotated) values ty reveals `Literal[1]` where mypy reveals `int` (or `Literal[1]?`). The spec "
        "leaves literal widening of inferred types to implementations. Bug only if a runtime value falls outside the "
        "literal type or a declared type is ignored.",
        (K.REVEAL_MISMATCH,), m_literal_widening, auto=True, runtime_override=True,
    ),
    KBEntry(
        "JOIN-VS-UNION", "mypy joins where ty builds unions (tracked mypy issue class)", Dismissal.KNOWN_LIMITATION,
        "https://github.com/python/mypy/issues?q=is%3Aopen+label%3Atopic-join-v-union",
        "mypy infers e.g. `[1, 'a']` as `list[object]` / `{'1': 2, 3: 4}` as `dict[object, int]` (join); ty/pyright "
        "infer unions. The spec does not specify inference of unannotated literals; mypy tracks moving to unions under "
        "its `topic-join-v-union` label (see also pyright's mypy-comparison doc). A pure reveal difference is logged, "
        "not filed. A *false positive* that mypy's join causes is NOT covered by this entry.",
        (K.REVEAL_MISMATCH,), m_join_union, auto=True, runtime_override=True,
    ),
    KBEntry(
        "PRECISION-RUNTIME-CONSISTENT", "one checker infers a strictly more precise type that CPython confirms",
        Dismissal.DESIGN_DIVERGENCE, "https://typing.python.org/en/latest/spec/concepts.html",
        "Outside spec-defined narrowing constructs, how precisely a checker infers a type (e.g. narrowing to the "
        "assigned value on `y: int | None = None`) is implementation-defined; both answers are sound if every observed "
        "runtime value inhabits the more precise type.",
        (K.REVEAL_MISMATCH,), m_precision_runtime_consistent, auto=True, runtime_override=True,
    ),
    KBEntry(
        "MYPY-SKIPS-UNREACHABLE", "mypy does not analyse code it considers unreachable", Dismissal.DESIGN_DIVERGENCE,
        "https://mypy.readthedocs.io/en/stable/common_issues.html#unreachable-code",
        "mypy silently skips blocks it deems unreachable (no reveal_type output); ty still reveals there. Confirmed "
        "unreachable by CPython coverage (the line never ran).",
        (K.REVEAL_UNPAIRED,), m_mypy_skips_unreachable, auto=True,
    ),
    KBEntry(
        "REACHABILITY-VS-COVERAGE", "a checker treats code as unreachable that CPython executed", Dismissal.DESIGN_DIVERGENCE,
        "https://docs.astral.sh/ty/features/type-system/#reachability-based-on-types",
        "HINT ONLY: one checker produced no reveal at a line that CPython executed - the checker considers reachable "
        "code unreachable, which silently disables checking there (soundness hazard). Usually a bug unless caused by "
        "documented unsound narrowing or NoReturn misuse.",
        (K.REVEAL_UNPAIRED,), m_unreachable_but_executed,
    ),
    KBEntry(
        "ENV-IMPORT", "import resolution / environment difference", Dismissal.CONFIG_ARTIFACT,
        f"{TY_DOCS}/modules/",
        "Unresolved/untyped imports depend on the environment; generated programs must use the standard library only.",
        (K.ONLY_MYPY, K.ONLY_TY, K.CONCERN_MISMATCH), m_env_import, auto=True, runtime_override=False,
    ),
    KBEntry(
        "SUPPRESSION-SEMANTICS", "type: ignore[code] semantics differ by design", Dismissal.DESIGN_DIVERGENCE,
        f"{TY_DOCS}/suppression/#standard-suppression-comments",
        "`# type: ignore[code]` suppresses only mypy codes in mypy; ty ignores codes without a `ty:` prefix (and "
        "`type: ignore[ty:rule]` is not a mypy code). The discrepancy is the documented behaviour.",
        (K.ONLY_MYPY, K.ONLY_TY), m_suppression_expected, auto=True, runtime_override=False,
    ),
    KBEntry(
        "SUPPRESSION-LINE", "discrepancy on a line with a suppression comment", Dismissal.DESIGN_DIVERGENCE,
        f"{TY_DOCS}/suppression/",
        "HINT: the statement carries a suppression comment. Check whether each tool honoured its documented "
        "suppression semantics; a tool ignoring its own suppression is a DIAGNOSTIC_DEFECT.",
        (K.ONLY_MYPY, K.ONLY_TY, K.CONCERN_MISMATCH), m_on_ignore_line,
    ),
    KBEntry(
        "INFERENCE-DOWNSTREAM", "error caused by differently *inferred* type of an unannotated variable",
        Dismissal.DESIGN_DIVERGENCE, "https://github.com/microsoft/pyright/blob/main/docs/mypy-comparison.md",
        "A reveal probe shows an unannotated operand inferred differently (join vs union, literal widening). The "
        "downstream accept/reject difference follows from implementation-defined inference, not a checking bug.",
        (K.ONLY_MYPY, K.ONLY_TY, K.CONCERN_MISMATCH), m_inference_downstream, auto=True, runtime_override=True,
    ),
    KBEntry(
        "GRADUAL-OPERAND", "an operand is Any/Unknown/@Todo in one checker", Dismissal.DESIGN_DIVERGENCE,
        f"{TY_DOCS}/reference/typing-faq/#what-is-the-unknown-type-and-when-does-it-appear",
        "HINT: a reveal probe shows a gradual type for an operand in the silent checker. Silence caused by a legitimately "
        "gradual operand (unannotated source, untyped decorator) is not a bug; Unknown where an annotation fixes the "
        "type IS an inference bug.",
        (K.ONLY_MYPY, K.ONLY_TY, K.CONCERN_MISMATCH), m_gradual_operand,
    ),
    KBEntry(
        "ERROR-CASCADE", "possible cascade from an earlier error", Dismissal.NOISE,
        "https://typing.python.org/en/latest/spec/",
        "HINT: the same checker already reported an error at a statement that binds a name used here; error recovery "
        "after a first error is implementation-defined.",
        (K.ONLY_MYPY, K.ONLY_TY, K.CONCERN_MISMATCH), m_cascade,
    ),
    KBEntry(
        "STUB-SKEW", "possible typeshed version skew", Dismissal.CONFIG_ARTIFACT,
        f"{TY_DOCS}/reference/configuration/#typeshed",
        "HINT: mypy and ty vendor different typeshed snapshots. If a stdlib signature is involved, re-run both with the "
        "same `--custom-typeshed-dir` / `--typeshed` before blaming either checker.",
        (K.ONLY_MYPY, K.ONLY_TY, K.CONCERN_MISMATCH), m_stdlib_call,
    ),
    KBEntry(
        "PARTIAL-TYPES", "empty-collection / None initialiser inferred from later use", Dismissal.DESIGN_DIVERGENCE,
        "https://mypy.readthedocs.io/en/stable/type_inference_and_annotations.html",
        "HINT: the variable starts as `[]`/`{}`/`None` and its type is completed by later statements (mypy 'partial "
        "types'); the scope and timing of this inference differ between checkers.",
        (K.ONLY_MYPY, K.ONLY_TY, K.REVEAL_MISMATCH), m_partial_types,
    ),
]
def _open_typeddict_kwargs(s, d) -> bool:
    """The statement calls a function whose **kwargs is Unpack[TD] with TD a TypedDict that is neither
    closed=True nor has extra_items= (those are checked strictly and are not covered by ty#4212)."""
    if not s.amap.tree:
        return False
    strict = {n.name for n in ast.walk(s.amap.tree) if isinstance(n, ast.ClassDef)
              and any(k.arg in ("closed", "extra_items") for k in n.keywords)}
    open_fns = set()
    for n in ast.walk(s.amap.tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.args.kwarg is not None:
            ann = n.args.kwarg.annotation
            if isinstance(ann, ast.Subscript) and getattr(ann.value, "id", getattr(ann.value, "attr", "")) == "Unpack":
                if getattr(ann.slice, "id", None) not in strict:
                    open_fns.add(n.name)
    node = _stmt_node(s, d)
    if node is None or isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    return any(isinstance(c, ast.Call) and getattr(c.func, "id", getattr(c.func, "attr", None)) in open_fns
               for c in ast.walk(node))


_REQUIRES = {"open_typeddict_kwargs": _open_typeddict_kwargs}


def _upstream_entries() -> list[KBEntry]:
    path = Path(__file__).parent / "data" / "known_upstream.json"
    if not path.exists():
        return []
    out = []
    for e in json.loads(path.read_text()).get("entries", []):
        kind = K(e["kind"])

        def matcher(s, d, e=e):
            diags = d.mypy if e["kind"] == "only_mypy" else d.ty if e["kind"] == "only_ty" else d.mypy + d.ty
            if e["kind"] == "only_ty" and e.get("silent_tool") == "ty":
                diags = d.pyright  # pyright-only concern that ty (and mypy) miss
            hit = [x for x in diags if (not e.get("codes") or (x.code or "") in e["codes"])
                   and re.search(e.get("message", ""), x.message)]
            if not hit:
                return False
            if e.get("statement") and not re.search(e["statement"], d.statement):
                return False
            if e.get("source") and not re.search(e["source"], s.source):
                return False
            req = _REQUIRES.get(e.get("requires", ""))
            return req(s, d) if req else True

        out.append(KBEntry(
            f"UPSTREAM-{e['id']}", f"already reported upstream: {e['note']}", Dismissal(e["dismissal"]), e["url"],
            f"{e['note']} ({e['url']}). Known issue - do not file again; add new variants as a comment if they "
            "add information.", (kind,), matcher, auto=True, runtime_override=False,
        ))
    return out


ENTRIES[:0] = _upstream_entries()  # checked first: an exact upstream match beats a generic explanation
BY_ID = {e.id: e for e in ENTRIES}


def matching_entries(s: CaseState, d: Discrepancy) -> list[KBEntry]:
    out = []
    for e in ENTRIES:
        if d.kind in e.kinds:
            try:
                if e.matcher(s, d):
                    out.append(e)
            except Exception:  # noqa: BLE001 - a broken matcher must never break adjudication
                continue
    return out


def kb_prompt_block(ids: list[str]) -> str:
    return "\n\n".join(BY_ID[i].prompt_text() for i in ids if i in BY_ID)


def tracking_issue_for(d: Discrepancy) -> list[str]:
    missing = mypy_checks_without_ty_equivalent()
    out = []
    for x in d.mypy:
        row = missing.get(x.code or "")
        if row:
            out.extend(row.issues)
    return out


__all__ = ["ENTRIES", "BY_ID", "KBEntry", "matching_entries", "kb_prompt_block", "runtime_contradiction",
           "tracking_issue_for", "rule_rows", "META_CODES"]
