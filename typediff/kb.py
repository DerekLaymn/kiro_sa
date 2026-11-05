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
from .experiments import MYPY_CODE_ENABLERS, ExperimentRunner, self_call_plan
from .inhabit import inhabits
from .models import Discrepancy, DiscrepancyKind, Dismissal, Evidence, EvidenceType, Severity, Tool
from .parsers import classify_exception
from .selfparam import has_self_typed_state
from .state import CaseState
from .typenorm import (gradual_diff, has_bool_literal, is_join_vs_union, is_literal_retention, is_literal_widening,
                       normalize)

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
    # extra demotion beyond the CPython-contradiction switch: returns an explanation when the entry must NOT dismiss
    # this discrepancy (it then stays in the review queue with the explanation as a neutral note)
    demote: Callable[[CaseState, Discrepancy], str | None] | None = None
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
    verify.expects = lambda d: {"kind": "config_toggle", "tool": tool.value, "flags": flags}  # the entry's OWN experiment
    return verify


def entry_demotion(s: CaseState, d: Discrepancy, e: KBEntry) -> Evidence | None:
    """Evidence explaining why ``e`` must not dismiss ``d`` (CPython contradiction or the entry's own demotion), else None."""
    c = runtime_contradiction(s, d)
    if c and (e.runtime_override or d.kind in e.runtime_override_kinds):
        return Evidence(EvidenceType.RUNTIME, "bug", f"KB:{e.id} would explain this, but {c}", verified=True, strength="strong")
    note = e.demote(s, d) if e.demote is not None else None
    if note:
        return Evidence(EvidenceType.RUNTIME, "neutral", f"KB:{e.id} would explain this, but {note}", verified=True,
                        strength="medium")
    return None


def own_experiment_confirmed(d: Discrepancy, e: KBEntry, ex: ExperimentRunner | None) -> bool:
    """A verify-required entry may back a dismissal only with the experiment that belongs to ITS toggle: an ok result
    for this discrepancy, with the request this entry expects, whose outcome says the discrepancy went away."""
    expects = getattr(e.verify, "expects", None)
    if expects is None or ex is None:
        return False
    want = expects(d)
    return any(r.ok and r.discrepancy_id == d.id and all(r.request.get(k) == v for k, v in want.items())
               and (r.outcome.get("persists") is False or r.outcome.get("unchanged") is True) for r in ex.results)


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


def _mypy_optional_flags(d) -> list[str]:
    flags: list[str] = []
    for c in _optional_mypy_codes_for(d):
        flags += MYPY_CODE_ENABLERS.get(c, ["--enable-error-code", c])
    return flags


v_mypy_optional.expects = lambda d: {"kind": "config_toggle", "tool": "mypy", "flags": _mypy_optional_flags(d)}


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


def m_self_upper_bound(s, d):
    """Narrow, ALL required (see selfparam.match_self_param_call): a method has Self in a non-receiver parameter; mypy's
    arg-type rejection names a strict subclass as the expected type, no override in between; the rejected argument is
    the defining class or a supertype of the receiver; ty is silent."""
    return d.kind == K.ONLY_MYPY and self_call_plan(s, d) is not None


def demote_self_state_crash(s, d) -> str | None:
    """Self-typed attribute + a CPython type-related exception: the case where ty IS unsound (not 'intended')."""
    rt = s.runtime
    if has_self_typed_state(s.amap.tree) and rt.status == "exception" and classify_exception(rt.exc_type, rt.exc_message) == "strong":
        return (f"CPython raised {rt.exc_type}: {rt.exc_message} and the program keeps state in a Self-typed attribute "
                "(the PEP 673 `LinkedList.next: Self | None` / `list[Self]` pattern). ty specialises such attributes to the "
                "receiver while it solves a Self parameter jointly, so a base instance accepted by the call can end up in a "
                "slot ty believes holds the subclass. That unsoundness is NOT covered by the 'intended' verdict of ty#4656 "
                "(see ty#2255, discuss.python.org 86338): human review")
    return None


def v_self_desugar(s, d, ex):
    """Auto-dismissal only if re-running ty on the spec's own TypeVar desugaring gives the SAME answer."""
    if not s.online:
        return None
    r = ex.run(d, {"kind": "spec_desugar", "line": d.anchor})
    if not r.ok:
        return None  # inconclusive (failed run / unsupported shape) -> never a verdict
    if r.outcome.get("unchanged"):
        return Evidence(EvidenceType.EXPERIMENT, "not_bug",
                        f"{r.outcome['tool']}'s answer is unchanged after the Self -> bounded-TypeVar desugaring ({r.id}): "
                        "consistent with the spec's own desugaring", citation=r.id, verified=True, strength="medium")
    return Evidence(EvidenceType.EXPERIMENT, "neutral",
                    f"the answer changes under the desugaring ({r.id}) - KB explanation does not apply", citation=r.id,
                    verified=True, strength="medium")


v_self_desugar.expects = lambda d: {"kind": "spec_desugar", "line": d.anchor}


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


def _class_defs(s) -> dict[str, ast.ClassDef]:
    return {n.name: n for n in ast.walk(s.amap.tree) if isinstance(n, ast.ClassDef)} if s.amap.tree else {}


def _ancestors(name: str, classes: dict[str, ast.ClassDef]) -> set[str]:
    out, todo = {name}, [name]
    while todo:
        c = classes.get(todo.pop())
        for b in (c.bases if c else []):
            if isinstance(b, ast.Name) and b.id not in out:
                out.add(b.id)
                todo.append(b.id)
    return out


def _new_return_name(c: ast.ClassDef) -> str | None:
    for f in c.body:
        if isinstance(f, ast.FunctionDef) and f.name == "__new__" and f.returns is not None:
            r = f.returns
            return r.value if isinstance(r, ast.Constant) and isinstance(r.value, str) else getattr(r, "id", None)
    return None


def m_callable_join_union(s, d):
    """mypy `def () -> X` vs ty `<class A> | <class B>` and pyright `type[A] | type[B]` (same classes), where every
    member is X, derives from X, or has a source `__new__` returning X or a subclass of X."""
    if not (d.mypy and d.ty and d.pyright):
        return False
    from .typenorm import callable_join_vs_union, members_of_union_text

    base = callable_join_vs_union(d.mypy[0].revealed_type, d.ty[0].revealed_type, d.pyright[0].revealed_type)
    if base is None:
        return False
    base = base.rsplit(".", 1)[-1]
    classes = _class_defs(s)
    if base not in classes:
        return False
    for m in members_of_union_text(d.ty[0].revealed_type):
        m = m.rsplit(".", 1)[-1]
        if m not in classes:
            return False
        ret = _new_return_name(classes[m])
        if base not in _ancestors(m, classes) and not (ret and base in _ancestors(ret, classes)):
            return False
    return True


def demote_exception_at_statement(s, d) -> str | None:
    rt = s.runtime
    if rt.status == "exception" and classify_exception(rt.exc_type, rt.exc_message) == "strong" \
            and d.anchor in {s.amap.anchor(ln) for ln, _ in rt.frames}:
        return f"CPython raised {rt.exc_type}: {rt.exc_message} in this statement"
    return None


_NEW_RETURN = re.compile(r'Incompatible return type for "__new__" \(returns ".*", but must return a subtype of "(?P<cls>[\w.]+)"\)')


def m_new_returns_non_subtype(s, d):
    """mypy rejects `__new__` returning an unrelated type (python/mypy#15182) and reveals the class itself; ty and pyright
    reveal the returned type, equal to each other, and CPython's probe value inhabits it."""
    if not (d.mypy and d.ty and d.pyright):
        return False
    m, t, p = _rev(d, "mypy", s), _rev(d, "ty", s), (normalize(d.pyright[0].revealed_type, s.module)
                                                       if d.pyright[0].revealed_type is not None else None)
    if not (m and t and p) or t.text != p.text or t.text == m.text:
        return False
    hits = [_NEW_RETURN.search(x.message) for x in s.diags.get(Tool.MYPY, []) if x.code == "misc"]
    if not any(h and h["cls"].rsplit(".", 1)[-1] == m.text.rsplit(".", 1)[-1] for h in hits):
        return False
    pr = matched_probe(s, d, "ty")
    return pr is not None and inhabits(pr.shape, t, s.nominal_classes) is True


def _scope_bindings(scope: ast.AST, name: str):
    """(bare annotation lines, other binding lines) of ``name`` directly in ``scope`` (nested scopes skipped)."""
    bare, other = [], []
    todo = list(ast.iter_child_nodes(scope))
    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
        a = scope.args
        if any(p.arg == name for p in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg] if p is not None):
            other.append(0)
    while todo:
        n = todo.pop()
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == name:
            (bare if n.value is None else other).append(n.lineno)
            todo.extend(c for c in ast.iter_child_nodes(n) if c is not n.target)
            continue
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if n.name == name:
                other.append(n.lineno)
            continue  # nested scope
        elif isinstance(n, ast.Lambda):
            continue
        elif isinstance(n, ast.Name) and n.id == name and isinstance(n.ctx, (ast.Store, ast.Del)):
            other.append(n.lineno)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            if any((a.asname or a.name.split(".")[0]) == name for a in n.names):
                other.append(n.lineno)
        elif isinstance(n, (ast.Global, ast.Nonlocal)) and name in n.names:
            other.append(n.lineno)
        elif isinstance(n, ast.ExceptHandler) and n.name == name:
            other.append(n.lineno)
        elif isinstance(n, (ast.MatchAs, ast.MatchStar)) and getattr(n, "name", None) == name:
            other.append(n.lineno)
        todo.extend(ast.iter_child_nodes(n))
    return bare, other


_TY_UNDEF = re.compile(r"Name `(?P<n>\w+)` used when not defined")
_PYRIGHT_UNBOUND = re.compile(r'"(?P<n>\w+)" is (?:unbound|not defined)')


def m_annotation_only_read(s, d):
    """ty and pyright both say the name is unbound, mypy is silent, and the AST shows the name is only ever declared
    (bare `x: T`, no value) in its module/function scope - never assigned, imported, defined or passed in."""
    if not (d.ty and d.pyright and not d.mypy and s.amap.tree is not None):
        return False
    if not all(x.code == "unresolved-reference" for x in d.ty):
        return False
    hits = [(m["n"], x.line) for x in d.ty if (m := _TY_UNDEF.search(x.message))]
    names = {n for n, _ in hits}
    if not names or len(hits) != len(d.ty):
        return False
    if len(names) == 1:
        if not any("unbound" in x.message or "not defined" in x.message for x in d.pyright):
            return False
    else:  # several names on one statement (`u(D_C, A_C)`): pyright must name every one of them
        pr = {m["n"] for x in d.pyright if (m := _PYRIGHT_UNBOUND.search(x.message))}
        if not names <= pr:
            return False
    chain = s.amap.enclosing_nodes(d.anchor)
    scope = next((n for n in reversed(chain[:-1]) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))),
                 s.amap.tree)
    if isinstance(scope, ast.ClassDef):
        return False
    for name in names:  # every name must be declared-only in this scope, before its (first) flagged use
        bare, other = _scope_bindings(scope, name)
        if not (bare and not other and min(bare) < min(line for n, line in hits if n == name)):
            return False
    return True


_TODO_SHOULD_ERROR = re.compile(r"#\s*TODO\b.*should\s+(?:\w+\s+)?error", re.I)


def m_mdtest_todo(s, d):
    """A `# TODO: should error ...` comment within the 3 lines above the flagged statement."""
    lo = d.anchor
    window = s.amap.lines[max(0, lo - 4):lo - 1]
    return any(_TODO_SHOULD_ERROR.search(x) for x in window)


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
    tool = "ty" if d.reveal_relation == "ty_more_precise" else "mypy"
    precise = _rev(d, tool, s)
    p = matched_probe(s, d, tool)  # the probe of THIS reveal_type call; None when the pairing is ambiguous -> adjudicate
    return p is not None and inhabits(p.shape, precise, s.nominal_classes) is True


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
        if has_bool_literal(m.node) or has_bool_literal(t.node):
            continue  # Literal[True]/[False] = a tool EVALUATED an expression; CPython can contradict it (stage 3 round 2)
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
    KBEntry(
        "TY-SELF-UPPER-BOUND", "ty solves Self in a method signature as a TypeVar bounded by the defining class",
        Dismissal.DESIGN_DIVERGENCE, "https://github.com/astral-sh/ty/issues/4656",
        "ty treats `Self` in a method signature as a TypeVar whose upper bound is the defining class and solves it "
        "jointly with the receiver (the typing spec's own desugaring `def m(self: T, c: T) -> T`). So an inherited, "
        "non-overridden `Leaf().add(Node())` with `def add(self, c: Self)` is accepted with `Self = Node`; mypy and pyright "
        "pin `Self` to the receiver (`Leaf`) and reject it. The spec is ambiguous here: ty#4656 (reported by us, closed as intended "
        "behaviour / design divergence, not a bug; the reveal_type display of the bound method is the display bug, ty#4673), ty#1172 (the earlier design discussion), "
        "ty#2255 (the missing Liskov check on overrides that take `Self`), discuss.python.org 'Unsoundness of "
        "contravariant Self type' (86338). Fires only when ALL hold: Self sits in a non-receiver parameter, mypy's "
        "rejection names a strict subclass as the expected type with no override in between, the rejected argument is "
        "the defining class or a supertype of the receiver, and ty is silent. It dismisses ONLY after a deterministic "
        "desugar probe shows ty answers the same on the spec's TypeVar form. NOT covered: a crash that goes through "
        "Self-typed state (`LinkedList.next: Self | None`, `list[Self]`) - ty is genuinely unsound there, so the entry "
        "steps aside and the case goes to review.",
        (K.ONLY_MYPY,), m_self_upper_bound, auto=True, runtime_override=True, verify=v_self_desugar,
        demote=demote_self_state_crash,
        example="from typing import Self\n\n\nclass Node:\n    def add(self, c: Self) -> Self:\n        return self\n\n\n"
                "class Leaf(Node):\n    pass\n\n\nx = Leaf()\nx.add(Node())\n",
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


def _rebound_inferred_lambda(s, d) -> bool:
    """Narrow mypy#9658 match: inferred lambda captures an optional parameter,
    narrowed by an earlier None check and then explicitly rebound to None.
    Other closure patterns must still be investigated independently.
    """
    node = _stmt_node(s, d)
    if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Lambda) or not s.amap.tree:
        return False
    body = node.value.body
    if not (isinstance(body, ast.BinOp) and isinstance(body.op, ast.Add)
            and isinstance(body.left, ast.Name) and isinstance(body.right, ast.Constant)
            and isinstance(body.right.value, int)):
        return False
    captured = {body.left.id}
    captured -= {a.arg for a in node.value.args.posonlyargs + node.value.args.args + node.value.args.kwonlyargs}
    for fn in ast.walk(s.amap.tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)) or node not in fn.body:
            continue
        index = fn.body.index(node)
        for arg in fn.args.posonlyargs + fn.args.args + fn.args.kwonlyargs:
            if arg.arg not in captured or arg.annotation is None:
                continue
            ann = arg.annotation
            optional = any(isinstance(n, ast.Constant) and n.value is None for n in ast.walk(ann)) or (
                isinstance(ann, ast.Subscript) and getattr(ann.value, "id", "") == "Optional")
            if not optional:
                continue
            rebound = any(isinstance(st, ast.Assign) and isinstance(st.value, ast.Constant) and st.value.value is None
                          and any(isinstance(t, ast.Name) and t.id == arg.arg for t in st.targets)
                          for st in fn.body[index + 1:])
            narrowed = any(isinstance(st, ast.If) and isinstance(st.test, ast.Compare)
                           and isinstance(st.test.left, ast.Name) and st.test.left.id == arg.arg
                           and len(st.test.ops) == 1 and isinstance(st.test.ops[0], ast.Is)
                           and isinstance(st.test.comparators[0], ast.Constant) and st.test.comparators[0].value is None
                           and any(isinstance(assign, ast.Assign) and isinstance(assign.value, ast.Constant)
                                   and assign.value.value is not None
                                   and any(isinstance(t, ast.Name) and t.id == arg.arg for t in assign.targets)
                                   for assign in st.body)
                           for st in fn.body[:index])
            if rebound and narrowed:
                return True
    return False


def _origin_status(s: CaseState, d: Discrepancy):
    from . import origin

    if d.kind != K.REVEAL_MISMATCH:
        return None
    return origin.status(s.source, s.module, d.mypy, d.ty)


def m_origin_oracle_reveal(s, d):
    """Narrow: the program carries its origin suite's expectation for this exact reveal; the ORIGIN tool matches it, the
    other tool does not, and the other tool's answer is only LESS precise (more Any/Unknown parts than the blessed
    answer; or, for a precision relation, the blessed answer is the more precise one). Never a different/uncomparable
    type, never an accept/reject difference."""
    from . import origin

    st = _origin_status(s, d)
    if st is None or not st["match"][st["origin"]] or st["match"]["mypy" if st["origin"] == "ty" else "ty"]:
        return False
    if _chain_tags(s, d) & _SPEC_NARROWING:
        return False  # narrowing results are (partly) specified: a more/less precise answer there needs a judge
    other = "mypy" if st["origin"] == "ty" else "ty"
    other_text = (d.mypy if other == "mypy" else d.ty)[0].revealed_type
    # Only the gradual relation. A more precise answer by the origin tool, blessed by its own suite, is circular
    # evidence (review kbloop round 2): it stays in review and ORIGIN-ORACLE-NOTE explains it.
    return d.reveal_relation == "gradual" and origin.other_is_less_precise(st["expected"], other_text, s.module)


def m_origin_oracle_note(s, d):
    st = _origin_status(s, d)
    return bool(st and st["match"][st["origin"]] and not st["match"]["mypy" if st["origin"] == "ty" else "ty"])


def m_origin_mismatch(s, d):
    st = _origin_status(s, d)
    return bool(st and not st["match"][st["origin"]])


def _annotation_roots(node: ast.AST) -> list[ast.AST]:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        a = node.args
        return [x.annotation for x in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg]
                if x is not None and x.annotation is not None] + ([node.returns] if node.returns is not None else [])
    if isinstance(node, ast.AnnAssign):
        return [node.annotation]
    return []


_TY_UNDEF_NAME = re.compile(r"Name `(\w+)` used when not defined")


def _unquoted_forward_ref(s, d) -> bool:
    """python/mypy#948: mypy does not require string-literal escapes for forward references. Narrow: no
    `from __future__ import annotations` in the program; every name ty reports undefined at this statement is an
    UNQUOTED name inside an annotation of this very statement and names a class of this file that is defined later or
    whose body encloses the statement; pyright (when it ran) reports the same name undefined."""
    tree = s.amap.tree
    if tree is None:
        return False
    # one-line `def f(x: B) -> None: ...` anchors on its body: use every def / annotated assignment starting on this line
    headers = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.AnnAssign))
               and d.anchor <= n.lineno <= d.anchor_end]
    if not headers:
        return False
    node = headers[0]
    if any(isinstance(n, ast.ImportFrom) and n.module == "__future__" and any(a.name == "annotations" for a in n.names)
           for n in ast.walk(tree)):
        return False
    if not re.match(r"(?:#[^\n]*\n){0,6}?#\s*origin:\s*python/mypy\b", s.source):
        # header must be in the first lines (harvester writes it at the top). Only for programs harvested from mypy's own (never executed) test-suite. A bug-report repro that has this
        # shape may hide a real bug behind the forward reference (calibration: python/mypy#7935), so it stays in review
        return False
    names = {m.group(1) for x in d.ty if (m := _TY_UNDEF_NAME.search(x.message))}
    if not names or len(names) != len(d.ty):
        return False
    unquoted = {n.id for h in headers for r in _annotation_roots(h) for n in ast.walk(r) if isinstance(n, ast.Name)}
    classes = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    line = getattr(node, "lineno", d.anchor)
    for name in names:
        c = classes.get(name)
        if name not in unquoted or c is None or not (c.lineno > line or c.lineno <= line <= (c.end_lineno or c.lineno)):
            return False
    if s.pyright_ran:
        pr = {m.group(1) for x in s.diags.get(Tool.PYRIGHT, []) if s.amap.anchor(x.line) == d.anchor
              for m in [re.search(r'"(\w+)" is (?:not defined|unbound)', x.message)] if m}
        if not names <= pr:
            return False
    return True


def _stmt_exprs(node: ast.AST | None) -> list[ast.AST]:
    """The expressions that belong to the statement itself (compound statements: header only, not their bodies)."""
    if node is None:
        return []
    if isinstance(node, (ast.If, ast.While)):
        return [node.test]
    if isinstance(node, (ast.For, ast.AsyncFor)):
        return [node.iter]
    if isinstance(node, (ast.With, ast.AsyncWith)):
        return [i.context_expr for i in node.items]
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Try, ast.Match)):
        return []
    return [node]


def _stmt_walk(s: CaseState, d: Discrepancy) -> list[ast.AST]:
    return [n for e in _stmt_exprs(_stmt_node(s, d)) for n in ast.walk(e)]


def _generic_typeddict_typevar_call(s, d) -> bool:
    """astral-sh/ty#4884: the statement calls a function whose parameter is a SUBSCRIPTED GENERIC TypedDict
    (Generic[..] base or PEP 695 parameters) over one of the function's own type variables, so the result type comes from
    solving that variable against the TypedDict argument (ty leaves it Unknown). An ordinary generic class, a
    TypedDict without a solved variable, or a statement without such a call do not match."""
    from . import crash_upstream as cu

    tree = s.amap.tree
    if tree is None:
        return False
    tds = {c.name for c in cu._classes(tree) if any(cu._head(b) == "TypedDict" for b in c.bases)
           and (cu._type_params(c) or any(cu._head(b) == "Generic" and isinstance(b, ast.Subscript) for b in c.bases))}
    if not tds:
        return False
    module_tv = set(cu._module_calls(tree, "TypeVar"))
    solving = set()
    for fn in cu._functions(tree):
        tvs = module_tv | {t.name for t in cu._type_params(fn, ast.TypeVar)}
        for p in cu._params(fn):
            if p.annotation is None:
                continue
            ann = cu._resolve(p.annotation)  # the TypedDict must be the parameter itself, not nested (that is ty#4803)
            if isinstance(ann, ast.Subscript) and cu._head(ann.value) in tds and cu._names(ann.slice) & tvs:
                solving.add(fn.name)
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in solving for n in _stmt_walk(s, d))


_BACKTICK_GENERIC = re.compile(r"`(\w+)\[")


def _callable_attr_contravariance(s, d) -> bool:
    """python/mypy#22339: mypy infers a PEP 695 class contravariant in T although it stores a mutable (non-Final, not
    underscore-private) Callable[[..T..], R] attribute (class-level annotation or `self.x = param`). The class is named
    in ty's message. Final attributes, methods and classes with other attribute shapes do not match."""
    from . import crash_upstream as cu

    tree = s.amap.tree
    if tree is None:
        return False
    named = {m.group(1) for x in d.ty for m in _BACKTICK_GENERIC.finditer(x.message)}

    def contra_callable(ann, tps) -> bool:
        for sub in cu._subs(cu._resolve(ann), "Callable"):
            elts = cu._slice_elts(sub)
            if len(elts) == 2 and isinstance(elts[0], ast.List) and cu._names(elts[0]) & tps \
                    and not cu._names(elts[1]) & tps:
                return True
        return False

    for c in cu._classes(tree):
        tps = {t.name for t in cu._type_params(c, ast.TypeVar)}
        if c.name not in named or not tps:
            continue
        for st in c.body:
            if (isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name) and not st.target.id.startswith("_")
                    and cu._head(st.annotation) != "Final" and contra_callable(st.annotation, tps)):
                return True
        for fn in cu._methods(c):
            ann = {p.arg: p.annotation for p in cu._params(fn) if p.annotation is not None}
            for n in ast.walk(fn):
                if (isinstance(n, ast.Assign) and isinstance(n.value, ast.Name) and n.value.id in ann
                        and contra_callable(ann[n.value.id], tps)
                        and any(isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self"
                                and not t.attr.startswith("_") for t in n.targets)):
                    return True
    return False


def _stale_index_narrowing(s, d) -> bool:
    """python/mypy#20969: mypy keeps the narrowing of a constant-index subscript (`xs[0] is not None`,
    `isinstance(t[0], int)`) after an ASSIGNMENT to that very subscript; the reported statement uses the subscript after
    the assignment. Attribute narrowing (mypy resets), non-constant indices and `del` are not covered."""
    from . import crash_upstream as cu

    tree = s.amap.tree
    if tree is None:
        return False
    fns = [f for f in cu._functions(tree) if f.lineno <= d.anchor <= (f.end_lineno or f.lineno)]
    scope = min(fns, key=lambda f: (f.end_lineno or 0) - f.lineno) if fns else tree

    def key(n) -> str | None:
        return ast.unparse(n) if (isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name)
                                  and isinstance(n.slice, ast.Constant)) else None

    narrowed: dict[str, int] = {}
    for n in ast.walk(scope):
        if isinstance(n, (ast.If, ast.While, ast.Assert)):
            for t in ast.walk(n.test):
                k = None
                if isinstance(t, ast.Compare) and all(isinstance(o, (ast.Is, ast.IsNot, ast.Eq, ast.NotEq)) for o in t.ops):
                    k = key(t.left)
                elif isinstance(t, ast.Call) and cu._head(t.func) == "isinstance" and t.args:
                    k = key(t.args[0])
                if k is not None:
                    narrowed[k] = min(narrowed.get(k, n.lineno), n.lineno)
    used = {key(n) for n in _stmt_walk(s, d)} - {None}
    for n in ast.walk(scope):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                k = key(t)
                if k in narrowed and k in used and narrowed[k] < n.lineno < d.anchor:
                    return True
    return False


def _flag_classes(tree: ast.AST) -> set[str]:
    from . import crash_upstream as cu

    return {c.name for c in cu._classes(tree) if any(cu._head(b) in ("Flag", "IntFlag") for b in c.bases)}


def _flag_is_chain(s, d) -> bool:
    """python/mypy#21937 (same root cause: a Flag is expanded into its members): the statement sits in the final
    `else` of an `if x is F.A: .. elif x is F.B: ..` (or `==`) chain over members of an enum.Flag / IntFlag subclass. The
    same chain over a plain Enum is not covered (mypy is right there)."""
    tree = s.amap.tree
    if tree is None:
        return False
    flags = _flag_classes(tree)
    if not flags:
        return False

    def member_test(t) -> bool:
        return (isinstance(t, ast.Compare) and len(t.ops) == 1 and isinstance(t.ops[0], (ast.Is, ast.Eq))
                and isinstance(t.comparators[0], ast.Attribute) and isinstance(t.comparators[0].value, ast.Name)
                and t.comparators[0].value.id in flags)

    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        chain, cur = [node], node
        while len(cur.orelse) == 1 and isinstance(cur.orelse[0], ast.If):
            cur = cur.orelse[0]
            chain.append(cur)
        if len(chain) < 2 or not cur.orelse or not all(member_test(c.test) for c in chain):
            continue
        if cur.orelse[0].lineno <= d.anchor <= max(x.end_lineno or x.lineno for x in cur.orelse):
            return True
    return False


def _flag_member_op(s, d) -> bool:
    """astral-sh/ty#876 (checklist item: enum expansion must not be performed for enum.Flag): the statement uses
    a bitwise combination of two members of a Flag / IntFlag subclass, directly or through a variable assigned from one."""
    tree = s.amap.tree
    if tree is None:
        return False
    flags = _flag_classes(tree)
    if not flags:
        return False

    def member(n) -> bool:
        return isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in flags

    def combo(n) -> bool:
        return (isinstance(n, ast.BinOp) and isinstance(n.op, (ast.BitOr, ast.BitAnd, ast.BitXor))
                and member(n.left) and member(n.right))

    nodes = _stmt_walk(s, d)
    if any(combo(n) for n in nodes):
        return True
    names = {n.id for n in nodes if isinstance(n, ast.Name)}
    return any(isinstance(a, ast.Assign) and combo(a.value)
               and any(isinstance(t, ast.Name) and t.id in names for t in a.targets) for a in ast.walk(tree))


_FLAG_LITERAL_ARG = re.compile(r'has incompatible type "(?P<cls>\w+)"; expected "Literal\[(?P=cls)\.\w+\]"')


def _flag_combo_literal_arg(s, d) -> bool:
    """astral-sh/ty#876 (same Flag-expansion item, mypy-only row): mypy rejects passing a Flag value to a
    `Literal[F.X]` parameter ([arg-type], the type named in the message is a Flag / IntFlag subclass of the program)
    and the statement uses a bitwise combination of two members of that Flag, directly or through a variable assigned
    from one. ty is silent because it expands the combination to `Literal[F.R, F.W]`, narrows it to Never and treats
    the line as unreachable. A plain Enum, a Flag value that is not a member combination, or another mypy message do
    not match."""
    tree = s.amap.tree
    if tree is None or not d.mypy:
        return False
    flags = _flag_classes(tree)
    for x in d.mypy:
        m = _FLAG_LITERAL_ARG.search(x.message)
        if not m or m["cls"] not in flags:
            return False
    return _flag_member_op(s, d)


_REQUIRES = {"flag_combo_literal_arg": _flag_combo_literal_arg,
             "open_typeddict_kwargs": _open_typeddict_kwargs,
             "rebound_inferred_lambda": _rebound_inferred_lambda,
             "unquoted_forward_ref": _unquoted_forward_ref,
             "generic_typeddict_typevar_call": _generic_typeddict_typevar_call,
             "callable_attr_contravariance": _callable_attr_contravariance,
             "stale_index_narrowing": _stale_index_narrowing,
             "flag_is_chain": _flag_is_chain,
             "flag_member_op": _flag_member_op}


def _upstream_entries() -> list[KBEntry]:
    path = Path(__file__).parent / "data" / "known_upstream.json"
    if not path.exists():
        return []
    out = []
    for e in json.loads(path.read_text()).get("entries", []):
        if e["kind"] == "crash":
            continue  # crash entries are matched from the pipeline (typediff/crash_upstream.py), not as KB entries
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
            "add information.", (kind,), matcher, auto=True, runtime_override=False, example=e.get("example", ""),
            # optional per entry: step aside when CPython raised a type-related exception in the very statement
            demote=demote_exception_at_statement if e.get("demote_on_exception") else None,
        ))
    return out


ENTRIES.extend([
    KBEntry(
        "ANNOTATION-ONLY-READ", "mypy has no definite-assignment check for annotation-only variables",
        Dismissal.KNOWN_LIMITATION, "https://github.com/python/mypy/issues/15416",
        "A bare `x: int` (no value) followed by a read: ty [unresolved-reference] and pyright (unbound) agree with CPython "
        "(NameError); mypy does not track definite assignment of declared-only names (reproduced on mypy 2.4.0 even with "
        "possibly-undefined and used-before-def enabled). This is a TRACKED, unimplemented mypy check, not a mypy design "
        "choice: python/mypy#15416 (open, 'Mypy not reporting \"undefined\" variable', the exact `number: int; print(number)` "
        "program), python/mypy#17373 (open, possibly-undefined misses variable annotations), python/mypy#4019 (open, binder "
        "should track declared-but-uninitialised names); #11342 was closed as a duplicate of #686. CPython's NameError at this "
        "statement is STRONG evidence that ty/pyright are right and mypy has the false negative (both "
        "kb.runtime_contradiction and rules.attach_runtime_evidence record it as strong, blaming the silent tool, "
        "mypy). The entry keeps runtime_override=False on purpose: that NameError confirms the REPORTING tool "
        "(ty) and is the very fact this tracked mypy limitation is about, so it is no reason to hold ty's "
        "diagnostic back. Fires only when the AST shows the name is only ever declared "
        "(never assigned, imported, defined or a parameter) in its module/function scope and ty and pyright agree. "
        "Forward references and truly undefined names are NOT covered.",
        (K.ONLY_TY,), m_annotation_only_read, auto=True, runtime_override=False,
        example="x: int\nprint(x)\n",
    ),
    KBEntry(
        "MYPY-15182-NEW-RETURNS", "mypy rejects __new__ returning an unrelated type; ty and pyright follow the returned type",
        Dismissal.DUPLICATE, "https://github.com/python/mypy/issues/15182",
        "mypy reports `Incompatible return type for \"__new__\" (returns X, but must return a subtype of C)` [misc] and "
        "reveals C(); ty and pyright reveal X (equal to each other) and CPython's value inhabits X. Tracked upstream as "
        "python/mypy#15182 (closed 2026-05-27); whether the fix is in mypy 2.4.0 is UNVERIFIED. mypy-side deviation, not a ty bug.",
        (K.REVEAL_MISMATCH,), m_new_returns_non_subtype, auto=True, runtime_override=False,
        example="class R:\n    def __new__(cls) -> int:\n        return 42\n\n    def __init__(self, x: str) -> None: ...\n\n\n"
                "reveal_type(R())\n",
    ),
    KBEntry(
        "JOIN-VS-UNION-CALLABLE", "mypy joins constructor callables where ty and pyright keep the union",
        Dismissal.DESIGN_DIVERGENCE, "https://github.com/python/mypy/issues?q=is%3Aopen+label%3Atopic-join-v-union",
        "mypy reveals `def () -> X` for a join of classes whose constructors return X; ty (`<class A> | <class B>`) and "
        "pyright (`type[A] | type[B]`) agree on the union of the same classes, which is assignable to mypy's join. The spec "
        "does not define joins. Requires X to be a class in the source that every member derives from or constructs.",
        (K.REVEAL_MISMATCH,), m_callable_join_union, auto=True, runtime_override=False,
        demote=demote_exception_at_statement,
        example="class Base2: ...\nclass Base: ...\nclass Foo(Base): ...\n\n\nclass A(Base2):\n    def __new__(cls) -> Foo: ...  # type: ignore\n\n\n"
                "class B(Base2):\n    def __new__(cls) -> Base: ...  # type: ignore\n\n\nfrom typing import TypeVar\n\nT = TypeVar('T')\n\n\n"
                "def join(x: T, y: T) -> T: ...\n\n\nreveal_type(join(A, Foo))\n",
    ),
    KBEntry(
        "MDTEST-TODO", "the source itself documents a missing diagnostic with `# TODO: should error`",
        Dismissal.KNOWN_LIMITATION, "https://github.com/astral-sh/ty/blob/main/crates/ty_python_semantic/resources/mdtest/call/functools_partial.md",
        "A `# TODO: should error` comment within 3 lines above the statement: the harvested ty mdtest records this as a known "
        "missing diagnostic (here: functools.partial over merged constructor signatures). Logged, not filed.",
        (K.RUNTIME_MISS, K.ONLY_MYPY), m_mdtest_todo, auto=True, runtime_override=False,
        example="from functools import partial\n\n\nclass MyClass:\n    def __new__(cls, x: int) -> 'MyClass':\n"
                "        return super().__new__(cls)\n\n    def __init__(self) -> None: ...\n\n\np = partial(MyClass, 1)\n"
                "# TODO: should error: [missing-argument] once constructor signatures are merged.\np()\n",
    ),
])
_EXPECTED_ERROR = re.compile(r"#\s*(?:E\??:|error\b|type:\s*ignore)|should\s+(?:generate|report|produce|emit)\s+an?\s+(?:\w+[- ])?error", re.I)


def m_suite_expects_error(s, d):
    """The program's own test-suite marks THIS statement as an expected error (`# E:` mypy, `# error:` ty, a pyright
    "This should generate an error" comment on the statement or the line above). Exactly one tool reports it."""
    lines = s.amap.lines[max(0, d.anchor - 2):d.anchor_end]
    return bool(re.search(r"^#\s*origin:", s.source, re.M)) and any(_EXPECTED_ERROR.search(x) for x in lines)


def m_suite_allow_empty_bodies(s, d):
    """The program came from mypy's own test-suite (header `# origin: python/mypy`, which mypy's runner runs with
    allow_empty_bodies=True) and every mypy diagnostic here is [empty-body]; ty is silent."""
    return (d.kind == K.ONLY_MYPY and bool(d.mypy) and all(x.code == "empty-body" for x in d.mypy)
            and bool(re.match(r"(?:#[^\n]*\n){0,6}?#\s*origin:\s*python/mypy\b", s.source)))


def m_pyright_reveal_kwarg(s, d):
    """pyright-only `reveal_type(x, expected_text=...)` / `expected_type=`: mypy rejects the extra keyword."""
    if d.kind != K.ONLY_MYPY or not d.mypy or s.amap.tree is None:
        return False
    if not all(x.code == "misc" and re.fullmatch(r'"reveal_type" expects 1 argument', x.message.strip()) for x in d.mypy):
        return False
    if any(isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == "reveal_type" for n in ast.walk(s.amap.tree)):
        return False  # a user-defined reveal_type is a different function
    calls = [n for n in ast.walk(s.amap.tree) if isinstance(n, ast.Call) and getattr(n.func, "id", getattr(n.func, "attr", "")) == "reveal_type"
             and d.anchor <= n.lineno <= d.anchor_end]
    return bool(calls) and all(any(k.arg in ("expected_text", "expected_type") for k in c.keywords) for c in calls)


_EXPECT_ERR = re.compile(r"#\s*error:\s*\[([\w-]+)\]")


def m_expected_error_oracle(s, d):
    """HINT (never dismisses): the ty mdtest this program came from marks THIS statement with `# error: [rule]` (same line or
    the line directly above) and ty reports exactly that rule, mypy is silent. ty's report is what its own suite expects, so
    the open question is mypy's silence (possible mypy false negative or a mypy-only leniency), not a ty false positive."""
    if d.kind != K.ONLY_TY or not d.ty or not re.search(r"^#\s*origin:\s*ruff mdtest\b", s.source, re.M):
        return False
    window = s.amap.lines[max(0, d.anchor - 2):d.anchor_end]
    expected = {m.group(1) for ln in window for m in _EXPECT_ERR.finditer(ln)}
    return bool(expected) and all((x.code or "") in expected for x in d.ty)


ENTRIES.extend([
    KBEntry(
        "EXPECTED-ERROR-ORACLE", "HINT: ty's own suite expects this exact error; the open question is mypy's silence",
        Dismissal.DESIGN_DIVERGENCE, "https://docs.astral.sh/ty/",
        "The ty mdtest this program was harvested from marks the statement with `# error: [rule]` and ty reports that rule. "
        "That makes ty's diagnostic an expected one (not a ty false positive). Whether mypy's silence is a false negative, "
        "a mypy-only leniency or reachability is still undecided: check the mypy side.",
        (K.ONLY_TY,), m_expected_error_oracle,
    ),
])


ENTRIES.extend([
    KBEntry(
        "PYRIGHT-REVEAL-EXPECTED-KWARG", "pyright-only reveal_type(x, expected_text=...) keyword", Dismissal.INVALID_TEST,
        "https://github.com/microsoft/pyright/blob/main/packages/pyright-internal/src/analyzer/typeEvaluator.ts",
        "pyright special-cases the keyword arguments `expected_text` and `expected_type` of reveal_type (typeEvaluator.ts, "
        "the reveal_type handler reads `arg.d.name.d.value === 'expected_text'` and `'expected_type'`, main branch, read "
        "2026-11). They are not part of typing.reveal_type(obj), so mypy reports `\"reveal_type\" expects 1 argument`. The seed "
        "uses a checker-specific API: harness noise, not a mypy bug. Fires only when every reveal_type call on the statement "
        "carries one of these keywords, the only mypy diagnostic is that message, and the program defines no reveal_type of its own.",
        (K.ONLY_MYPY,), m_pyright_reveal_kwarg, auto=True, runtime_override=False,
        example="def f(x: int) -> None:\n    if isinstance(x, int):\n        return\n    reveal_type(x, expected_text=\"Never\")\n",
    ),
])


ENTRIES.extend([
    KBEntry(
        "MYPY-SUITE-ALLOW-EMPTY-BODIES", "mypy's own test runner allows empty bodies; our default mypy run does not",
        Dismissal.CONFIG_ARTIFACT, "https://github.com/python/mypy/blob/v2.4.0/mypy/test/testcheck.py#L166",
        "mypy's check-*.test runner sets `options.allow_empty_bodies = not testcase.name.endswith(\"_no_empty\")` "
        "(mypy v2.4.0, mypy/test/testcheck.py line 166), so harvested mypy test programs written with `pass` bodies "
        "and non-None return types are clean under the suite's config. mypy documents [empty-body] as an error outside "
        "stubs/protocols/abstract methods (error_code_list.html, 'Check that functions don't have empty bodies outside "
        "stubs'). Fires only for a program whose header says `# origin: python/mypy`, only when every mypy diagnostic is "
        "[empty-body], and only after re-running mypy with --allow-empty-bodies makes the discrepancy disappear.",
        (K.ONLY_MYPY,), m_suite_allow_empty_bodies, auto=True, runtime_override=False,
        verify=_toggle(Tool.MYPY, ["--allow-empty-bodies"]),
        example="# origin: python/mypy check-classes.test [case testExample]\ndef f(x):\n    # type: (int) -> str\n    pass\n",
    ),
    KBEntry(
        "ORIGIN-ORACLE-REVEAL", "HINT: the origin suite blessed this reveal; the other tool is only less precise",
        Dismissal.DESIGN_DIVERGENCE, "https://typing.python.org/en/latest/spec/concepts.html#the-any-type",
        "The harvested program keeps its origin suite's own expectation comment (`# N: Revealed type is ...` for mypy, "
        "`# revealed: ...` for ty) for this very reveal_type call. The origin tool reproduces it; the other tool reveals "
        "a less precise answer (more Any/Unknown parts, or a supertype of the blessed type). A gradual or coarser answer "
        "is usually sound (spec: Any is compatible with every type), but nothing here verifies that the other answer is a "
        "supertype of the blessed one. Sorting aid only (review of kbloop round 2): it never closes a finding. Only "
        "the gradual relation; precision relations and different/uncomparable types are not matched.",
        (K.REVEAL_MISMATCH,), m_origin_oracle_reveal, auto=False, runtime_override=True,
    ),
    KBEntry(
        "SUITE-EXPECTS-ERROR", "HINT: the origin suite marks this statement as an expected error; only one tool reports it",
        Dismissal.NOISE, "https://typing.python.org/en/latest/spec/",
        "The harvested program says (by `# E:`, `# error:` or a 'should generate an error' comment) that an error is expected "
        "here. The tool that reports it agrees with the suite, so the silent tool has a false negative (a candidate for the "
        "silent tool's tracker, not a dismissal). Sorting aid only: it never closes a finding.",
        (K.ONLY_MYPY, K.ONLY_TY), m_suite_expects_error,
    ),
    KBEntry(
        "ORIGIN-ORACLE-NOTE", "HINT: the origin tool reproduces its suite's expectation, the other tool differs",
        Dismissal.DESIGN_DIVERGENCE, "https://typing.python.org/en/latest/spec/concepts.html",
        "The origin tool matches the expectation comment on this line and the other tool does not. Use it to explain "
        "and sort the queue; it does not say the other tool is wrong.",
        (K.REVEAL_MISMATCH,), m_origin_oracle_note,
    ),
    KBEntry(
        "ORIGIN-MISMATCH", "HINT: the origin tool does NOT reproduce its own suite's expectation (version skew / harvest)",
        Dismissal.INVALID_TEST, "https://typing.python.org/en/latest/spec/concepts.html",
        "The expectation comment on this line came from a suite that belongs to one of the two tools, and that tool's "
        "installed version does not reproduce it: the installed version differs from the suite's, the mdtest python-version "
        "was not honoured, or the harvest broke the program. A pipeline/harvest issue, not evidence of a tool bug.",
        (K.REVEAL_MISMATCH,), m_origin_mismatch,
    ),
])
_TY_ASSERT = re.compile(r"^Type `(?P<actual>.+)` does not match asserted type `(?P<asserted>.+)`$")
_MYPY_ASSERT = re.compile(r'^Expression is of type "(?P<actual>.+)", not "(?P<asserted>.+)"$')
_PYRIGHT_ASSERT = re.compile(r'^"assert_type" mismatch: expected "(?P<asserted>.+)" but received "(?P<actual>.+)"$')


def _declared_names(tree: ast.AST) -> set[str]:
    """Names that carry a declared type somewhere in the file: `x: T`, an annotated parameter."""
    out: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            out.add(n.target.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            a = n.args
            out |= {p.arg for p in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg]
                    if p is not None and getattr(p, "annotation", None) is not None}
    return out


def m_assert_type_literal_retention(s, d):
    """assert_type() compares INFERRED types; the failing tool's type is exactly the asserted type with its Literal parts
    kept (or widened). The spec leaves literal retention of inferred types open (literal.rst: "should the inferred type
    of x be str or Literal['blue']?"). Narrow: only assert_type diagnostics (every diagnostic on the statement),
    one-sided literal retention only, never a `Literal[True]`/`Literal[False]` type (that is a tool EVALUATING a
    comparison/operator, which CPython can contradict: reviewer round 1, ty folds `R((1,)) < (1,)` to Literal[False]
    where CPython gives True), pyright silent on the statement or reporting the same assert_type failure (any other
    pyright error, e.g. reportOperatorIssue, keeps the finding in review), no spec narrowing construct around the call,
    and the asserted expression is not a bare name with a declared type (a declared type that a tool ignores is a real
    bug)."""
    if d.kind not in (K.ONLY_TY, K.ONLY_MYPY) or s.amap.tree is None:
        return False
    diags, rx, code = (d.ty, _TY_ASSERT, "type-assertion-failure") if d.kind == K.ONLY_TY else (d.mypy, _MYPY_ASSERT, "assert-type")
    if not diags or any(x.code != code for x in diags):
        return False
    pairs = set()
    for x in diags:
        m = rx.match(x.message)
        a, b = (normalize(m["actual"], s.module), normalize(m["asserted"], s.module)) if m else (None, None)
        if not (a and b and is_literal_retention(a, b)):
            return False
        if has_bool_literal(a.node) or has_bool_literal(b.node):
            return False  # Literal[True]/Literal[False]: the tool EVALUATED a comparison/operator/call; that value is not "retention"
        pairs.add((a.text, b.text))
    if s.pyright_ran:  # pyright must be silent on the statement or agree with the failing tool (same actual/asserted types)
        for x in s.diags.get(Tool.PYRIGHT, []):
            if not (x.is_problem and d.anchor <= s.amap.anchor(x.line) <= d.anchor_end):
                continue
            m = _PYRIGHT_ASSERT.match(x.message) if x.code == "reportAssertTypeFailure" else None
            if not m or (normalize(m["actual"], s.module).text, normalize(m["asserted"], s.module).text) not in pairs:
                return False  # another pyright error (e.g. reportOperatorIssue) or a different answer: stays in review
    if _chain_tags(s, d) & _SPEC_NARROWING:
        return False  # narrowing results are (partly) specified: a different literal/non-literal answer there needs a judge
    node = _stmt_node(s, d)
    declared = _declared_names(s.amap.tree)
    calls = [c for c in ast.walk(node) if isinstance(c, ast.Call) and c.args
             and getattr(c.func, "id", getattr(c.func, "attr", None)) == "assert_type"] if node is not None else []
    if not calls:
        return False
    return not any(isinstance(c.args[0], ast.Name) and c.args[0].id in declared for c in calls)


def _name_declared_in_scope(scope: ast.AST, name: str) -> bool:
    """True if ``name`` is declared (annotation, any parameter, global/nonlocal) directly in ``scope``."""
    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
        a = scope.args
        if any(p.arg == name for p in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg] if p is not None):
            return True
    todo = list(ast.iter_child_nodes(scope))
    while todo:
        n = todo.pop()
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == name:
            return True
        if isinstance(n, (ast.Global, ast.Nonlocal)) and name in n.names:
            return True
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if n.name == name:
                return True  # a def/class binding is not an inferred variable
            continue
        if isinstance(n, ast.Lambda):
            continue
        if isinstance(n, (ast.Import, ast.ImportFrom)) and any((a.asname or a.name.split(".")[0]) == name for a in n.names):
            return True
        todo.extend(ast.iter_child_nodes(n))
    return False


def m_first_assignment_type(s, d):
    """mypy [assignment] on a re-bound, UNDECLARED variable: mypy fixes the variable's type at its first binding (its
    docs: "each name within a function only has a single 'declared' type"), ty and pyright infer a union of the bound
    types. Narrow: every mypy diagnostic is an `Incompatible types in assignment (expression has type ..., variable
    has type ...)` on a plain Assign/AugAssign to Name targets that have no declaration (annotation, parameter,
    global/nonlocal, def/class/import) in their scope; ty and pyright report nothing on the statement. The entry is
    verify-gated: it only dismisses when `mypy --allow-redefinition` makes the error disappear."""
    if d.kind != K.ONLY_MYPY or not d.mypy or s.amap.tree is None:
        return False
    if not all(x.code == "assignment" and x.message.startswith("Incompatible types in assignment (expression has type")
               and "base class" not in x.message for x in d.mypy):
        return False
    if any(x.is_problem and d.anchor <= s.amap.anchor(x.line) <= d.anchor_end for x in s.diags.get(Tool.PYRIGHT, [])):
        return False  # pyright also objects: the variable is declared or the assignment is genuinely wrong
    node = _stmt_node(s, d)
    if not isinstance(node, (ast.Assign, ast.AugAssign)):
        return False
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    if not targets or not all(isinstance(t, ast.Name) for t in targets):
        return False
    chain = s.amap.enclosing_nodes(d.anchor)
    scope = next((n for n in reversed(chain[:-1]) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))),
                 s.amap.tree)
    return not any(_name_declared_in_scope(scope, t.id) for t in targets)


def _reveal_arg_call(s, diag):
    """The reveal_type(...) call whose argument starts where this tool's reveal diagnostic points (both ty and mypy put
    the column of the reveal's ARGUMENT, 1-based), else None."""
    if diag.col is None or s.amap.tree is None:
        return None
    for c in ast.walk(s.amap.tree):
        if (isinstance(c, ast.Call) and getattr(c.func, "id", getattr(c.func, "attr", None)) == "reveal_type" and c.args
                and (c.args[0].lineno, c.args[0].col_offset + 1) == (diag.line, diag.col)):
            return c
    return None


def _error_inside_reveal_arg(s, tool: Tool, diag) -> bool:
    """True if ``tool`` reports an error INSIDE the argument of the reveal_type call that produced ``diag``."""
    call = _reveal_arg_call(s, diag)
    if call is None:
        return False
    arg = call.args[0]
    lo, hi = (arg.lineno, arg.col_offset + 1), (arg.end_lineno or arg.lineno, (arg.end_col_offset or 0) + 1)
    return any(x.is_problem and x.severity == Severity.ERROR and x.col is not None and lo <= (x.line, x.col) <= hi
               for x in s.diags.get(tool, []))


def _error_at_binding_of_reveal_arg(s, tool: Tool, diag) -> bool:
    """True if ``tool`` reports an ERROR on an EARLIER simple statement that binds a name read in the argument of the
    reveal_type call that produced ``diag`` (assignment target, unpacking, ``for``/``with`` target, def/class name).
    Compound statements count only through their own binding (def/class name, ``for`` target, ``with`` variables)."""
    call = _reveal_arg_call(s, diag)
    if call is None:
        return False
    names = {n.id for n in ast.walk(call.args[0]) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    if not names:
        return False
    here = s.amap.anchor(diag.line)
    for x in s.diags.get(tool, []):
        if not (x.is_problem and x.severity == Severity.ERROR) or s.amap.anchor(x.line) >= here:
            continue
        st = s.amap.stmt(x.line)
        node = st.node if st else None
        if node is None:
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound = {node.name}
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            bound = {n.id for n in ast.walk(node.target) if isinstance(n, ast.Name)}
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            bound = {n.id for i in node.items if i.optional_vars is not None for n in ast.walk(i.optional_vars)
                     if isinstance(n, ast.Name)}
        elif isinstance(node, (ast.If, ast.While, ast.Try, ast.Match)) or type(node).__name__ == "TryStar":
            continue
        else:
            bound = {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
        if bound & names:
            return True
    return False


def m_reveal_error_recovery(s, d):
    """One tool reveals exactly its gradual type (ty `Unknown`, mypy `Any`) for an expression in which that SAME tool
    reports an error, while the other tool reveals a type without gradual parts. The gradual reveal is the checker's
    error-recovery type, not an inference. The error itself is its own discrepancy (judged separately), so nothing is
    lost. Narrow: the error position lies inside the revealed argument, OR the same tool reported an error on an
    earlier statement that binds a name the revealed argument reads (the recovery type flows through the binding)."""
    if d.kind != K.REVEAL_MISMATCH or len(d.ty) != 1 or len(d.mypy) != 1:
        return False
    rt = s.runtime
    if rt.status == "exception" and d.anchor in {s.amap.anchor(ln) for ln, _ in rt.frames}:
        return False  # ANY CPython exception on this statement (also RuntimeError etc.) keeps the finding in review
    for tool, gradual, mine, other in ((Tool.TY, "Unknown", d.ty[0], d.mypy[0]), (Tool.MYPY, "Any", d.mypy[0], d.ty[0])):
        if (mine.revealed_type or "").strip() != gradual or not other.revealed_type:
            continue
        o = normalize(other.revealed_type, s.module)
        if o.node is None or "gradual" in o.flags or "todo" in o.flags:
            continue
        if _error_inside_reveal_arg(s, tool, mine) or _error_at_binding_of_reveal_arg(s, tool, mine):
            return True
    return False


def _scope_stores(scope: ast.AST, name: str) -> list[ast.AST]:
    """Statements in ``scope`` (nested scopes skipped) that bind ``name`` by plain/annotated/augmented assignment, or
    any other binding (``for``, ``with``, import, walrus, ...) represented by the binding node itself."""
    out, todo = [], list(ast.iter_child_nodes(scope))
    while todo:
        n = todo.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            if getattr(n, "name", None) == name:
                out.append(n)
            continue
        if isinstance(n, ast.Name) and n.id == name and isinstance(n.ctx, (ast.Store, ast.Del)):
            out.append(n)
        elif isinstance(n, (ast.Import, ast.ImportFrom)) and any((a.asname or a.name.split(".")[0]) == name for a in n.names):
            out.append(n)
        todo.extend(ast.iter_child_nodes(n))
    return out


def m_aliased_condition(s, d):
    """ty narrows `x` in `if alias:` where `alias = <condition on x>` (assigned once, before the `if`); mypy only narrows
    on the inline condition (python/mypy#13807, open feature request; pyright supports it too). The reveal is a
    precision difference (ty narrower). Narrow: the reveal sits inside an `if`/`while` whose test is exactly `alias` or
    `not alias`, `alias` is a local bound exactly once, by an assignment whose value contains the revealed expression."""
    if d.kind != K.REVEAL_MISMATCH or d.reveal_relation != "ty_more_precise" or len(d.ty) != 1 or s.amap.tree is None:
        return False
    call = _reveal_arg_call(s, d.ty[0])
    if call is None:
        return False
    target = ast.unparse(call.args[0])
    chain = s.amap.enclosing_nodes(d.anchor)
    for i, n in enumerate(chain):
        if not isinstance(n, (ast.If, ast.While)):
            continue
        test = n.test.operand if isinstance(n.test, ast.UnaryOp) and isinstance(n.test.op, ast.Not) else n.test
        if not isinstance(test, ast.Name):
            continue
        scope = next((c for c in reversed(chain[:i]) if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef))), s.amap.tree)
        stores = _scope_stores(scope, test.id)
        if len(stores) != 1:
            continue
        for a in ast.walk(scope):
            if (isinstance(a, (ast.Assign, ast.AnnAssign)) and a.value is not None and a.lineno < n.lineno
                    and any(isinstance(t, ast.Name) and t.id == test.id for t in (a.targets if isinstance(a, ast.Assign) else [a.target]))
                    and any(ast.unparse(x) == target for x in ast.walk(a.value))
                    and not _target_changed_between(scope, call.args[0], a, n)):
                return True
    return False


def _expr_root(e: ast.AST) -> str | None:
    """Leftmost name of an attribute / subscript chain (``a.b[0].c`` -> ``a``), else None."""
    while isinstance(e, (ast.Attribute, ast.Subscript)):
        e = e.value
    return e.id if isinstance(e, ast.Name) else None


def _target_changed_between(scope: ast.AST, target: ast.expr, alias_stmt: ast.stmt, if_stmt: ast.stmt) -> bool:
    """True if the aliased expression ``target`` may have changed between the alias assignment and the ``if``: any store
    (assignment, ``for``, ``with``, walrus, ``del``) to its root name or into it (``a.x = ..``, ``l[0] = ..``), and, for
    an attribute / subscript target, any call that mentions the root name (``a.clear()``, ``f(a)``)."""
    root = _expr_root(target)
    if root is None:
        return True  # not a name / attribute / subscript chain: cannot reason about it
    lo = (alias_stmt.end_lineno or alias_stmt.lineno, alias_stmt.end_col_offset or 0)
    hi = (if_stmt.lineno, if_stmt.col_offset)
    plain = isinstance(target, ast.Name)
    for n in ast.walk(scope):
        pos = (getattr(n, "lineno", None), getattr(n, "col_offset", None))
        if pos[0] is None or not (lo <= pos < hi):
            continue
        if isinstance(n, (ast.Name, ast.Attribute, ast.Subscript)) and isinstance(getattr(n, "ctx", None), (ast.Store, ast.Del)):
            if _expr_root(n) == root and (not plain or isinstance(n, ast.Name)):
                return True
        elif isinstance(n, ast.Call) and not plain and any(isinstance(x, ast.Name) and x.id == root for x in ast.walk(n)):
            return True
        elif isinstance(n, (ast.Import, ast.ImportFrom)) and any((a.asname or a.name.split(".")[0]) == root for a in n.names):
            return True
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == root:
            return True
    return False


_UNBOUND_OPT_IN_FLAGS = ["--enable-error-code", "possibly-undefined", "--enable-error-code", "used-before-def"]


def m_mypy_unbound_opt_in(s, d):
    """ty reports only `unresolved-reference` (Name `x` used when not defined) and mypy is silent. The pipeline then
    re-runs mypy with the two opt-in checks (``verify``); the hint is shown only when mypy reports the name there."""
    return (d.kind == K.ONLY_TY and bool(d.ty) and not d.mypy
            and all(x.code == "unresolved-reference" and _TY_UNDEF.search(x.message) for x in d.ty))


ENTRIES.extend([
    KBEntry(
        "MYPY-UNBOUND-OPT-IN-CHECK", "mypy opt-in check catches this; default-off",
        Dismissal.KNOWN_LIMITATION, "https://mypy.readthedocs.io/en/stable/error_code_list2.html",
        "HINT ONLY, never dismisses. ty reports an unbound / possibly-unbound name and mypy is silent by default, but "
        "mypy reports the same name when re-run with `--enable-error-code possibly-undefined --enable-error-code "
        "used-before-def` (mypy docs, error_code_list2: possibly-undefined is generated only with "
        "`--enable-error-code possibly-undefined`). The difference is a default-off mypy check, so mypy is not wrong "
        "to be silent by default. When mypy stays silent even with both checks on, the hint is NOT shown: that is a "
        "true mypy false negative (python/mypy#15416 annotation-only reads, forward references in class bases and "
        "bodies). A CPython NameError/UnboundLocalError on the name is strong evidence that ty is right either way.",
        (K.ONLY_TY,), m_mypy_unbound_opt_in, auto=False, runtime_override=False,
        verify=_toggle(Tool.MYPY, _UNBOUND_OPT_IN_FLAGS),
    ),
    KBEntry(
        "MYPY-13807-ALIASED-CONDITIONS", "mypy does not narrow through an aliased condition; ty and pyright do",
        Dismissal.KNOWN_LIMITATION, "https://github.com/python/mypy/issues/13807",
        "`is_none = x is None; if is_none: reveal_type(x)`: ty and pyright narrow `x` to `None`, mypy keeps the declared "
        "type, while the inline `if x is None:` narrows in all three (checked on mypy 2.4.0, ty 0.0.84). python/mypy#13807 "
        "(open, label 'feature': 'Add support for control flow analysis of aliased conditions') tracks the missing mypy "
        "feature; TypeScript 4.4 and pyright implement it. The typing spec leaves narrowing beyond the listed forms to "
        "implementations, and mypy's wider answer is sound. Fires only for a ty_more_precise reveal inside an `if`/`while` "
        "whose test is exactly `alias` / `not alias`, where `alias` is bound once, before the `if`, by an assignment "
        "whose value contains the revealed expression. A CPython value outside ty's narrower type keeps it in review.",
        (K.REVEAL_MISMATCH,), m_aliased_condition, auto=True, runtime_override=True,
        example="def f(x: int | None) -> None:\n    is_none = x is None\n    if is_none:\n        reveal_type(x)\n",
    ),
    KBEntry(
        "REVEAL-ERROR-RECOVERY", "a checker reveals its error-recovery type for an expression it reports an error in",
        Dismissal.NOISE, f"{TY_DOCS}/reference/typing-faq/#what-is-the-unknown-type-and-when-does-it-appear",
        "ty documents `Unknown` as 'a type that could not be fully inferred' (an unresolved name or import reveals "
        "Unknown), and mypy gives an erroneous expression the type Any; both behave as Any (spec concepts.rst: Any is "
        "compatible with every type). When a tool reveals exactly that gradual type for an expression in which it ALSO "
        "reports an error, the reveal says nothing about inference: the error is the finding, and it is judged as its "
        "own discrepancy. Fires only when one side is exactly `Unknown` (ty) / `Any` (mypy), the other side has no "
        "gradual part, and the same tool either reports an error inside the revealed argument, or reported an error "
        "on an EARLIER statement that binds a name the argument reads (`a, b, *c = 'x'` then `reveal_type(a)`: the "
        "recovery type flows through the binding; mypy's `Any` after an invalid assignment/class/def is the mirror). "
        "A CPython exception at the statement keeps it in review.",
        (K.REVEAL_MISMATCH,), m_reveal_error_recovery, auto=True, runtime_override=True,
        example="def g(a: int, b: str) -> None:\n    reveal_type(a + b)\n",
    ),
    KBEntry(
        "ASSERT-TYPE-LITERAL-RETENTION", "assert_type fails only because one tool keeps (or widens) inferred Literal types",
        Dismissal.DESIGN_DIVERGENCE, "https://typing.python.org/en/latest/spec/literal.html",
        "assert_type(val, T) asks whether the INFERRED type of val is equivalent to T (directives.rst). Whether the "
        "inferred type of an unannotated value keeps its Literal parts is left open by the spec (literal.rst, 'should the "
        "inferred type of x be str or Literal[\"blue\"]?'; mypy documents the context-sensitive `Literal[19]?` it keeps "
        "for Final names). The python/typing conformance suite says the same in tests/generics_scoping.py: for "
        "`assert_type(fun_1(1), int)` and `assert_type(fun_1(1), Literal[1])` 'One of these two should pass; either is "
        "acceptable'. The suite the assertion came from encodes ONE checker's choice, so another checker that "
        "answers with the literal-widened (or literal-keeping) type fails the assertion without any unsoundness. Fires "
        "only for assert_type diagnostics where the failing tool's type is exactly the asserted type with Literal parts "
        "kept or widened (nested too) and neither side contains Literal[True]/Literal[False] (a tool that evaluates a "
        "comparison or operator can be wrong, and CPython can show it), the other checkers are silent (mypy/ty by the "
        "discrepancy kind; pyright must be silent on the statement or report the very same assert_type mismatch, so "
        "e.g. a pyright reportOperatorIssue keeps the finding visible), no narrowing construct surrounds the call and the "
        "asserted expression is not a declared name. A runtime exception at the statement keeps it in review.",
        (K.ONLY_TY, K.ONLY_MYPY), m_assert_type_literal_retention, auto=True, runtime_override=True,
        example="from typing import Any, assert_type\n\nassert_type(slice(1234, None), \"slice[int, Any, Any]\")\n",
    ),
    KBEntry(
        "MYPY-FIRST-ASSIGNMENT-TYPE", "mypy fixes an undeclared variable's type at its first assignment; ty and pyright infer a union",
        Dismissal.DESIGN_DIVERGENCE, "https://mypy.readthedocs.io/en/stable/common_issues.html#redefinitions-with-incompatible-types",
        "mypy: 'Each name within a function only has a single declared type' - `n = 1; n = 'x'` is an [assignment] error "
        "unless `--allow-redefinition` (command_line.rst) is on. ty and pyright treat an unannotated variable's type as "
        "the union of its assigned types, so the later assignment is accepted. Documented mypy behaviour, not a ty "
        "false negative. Fires only for [assignment] on a plain Assign/AugAssign to undeclared Name targets with pyright "
        "silent, and only after re-running mypy with --allow-redefinition makes the discrepancy disappear. Declared "
        "variables (`x: int = 1; x = 's'`, annotated parameters) are NOT covered: ty reports those too.",
        (K.ONLY_MYPY,), m_first_assignment_type, auto=True, runtime_override=True,
        verify=_toggle(Tool.MYPY, ["--allow-redefinition"]),
        example="def f(flag: bool) -> None:\n    y = 1\n    if flag:\n        y = \"s\"\n    print(y)\n",
    ),
])
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


__all__ = ["ENTRIES", "BY_ID", "KBEntry", "matching_entries", "kb_prompt_block", "runtime_contradiction", "matched_probe",
           "entry_demotion", "own_experiment_confirmed", "tracking_issue_for", "rule_rows", "META_CODES"]
