"""Deterministic experiments the pipeline (or the LLM) can request to settle a discrepancy.

Every experiment re-runs real tools; nothing here is LLM-judged. LLM-requested experiments
are validated against allow-lists first (LLM output is untrusted input).

Kinds
-----
config_toggle   re-run one checker with a documented flag      -> "does the discrepancy survive?"
reveal_probe    insert reveal_type(expr) before a statement     -> operand types in mypy/ty/pyright/CPython
metamorphic     pep604 | pep585 | any_substitution rewrite      -> SELF_CONTRADICTION oracle
variant         LLM-authored program + stated relation          -> raw outcomes (medium strength)
witness         append code that should crash at runtime        -> RUNTIME proof of unsoundness
pyright         tie-breaker run                                 -> CONSENSUS (weak)
"""

from __future__ import annotations

import ast
import copy
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .anchors import AnchorMap
from .concerns import family
from .discrepancy import META_CODES, find_discrepancies, rel_name
from .inhabit import inhabits
from .models import Diagnostic, Discrepancy, DiscrepancyKind, Evidence, EvidenceType, Tool
from .parsers import classify_exception
from .typenorm import Relation, normalize, relation

if TYPE_CHECKING:
    from .pipeline import CaseState

ALLOWED_TY_FLAGS = {
    ("--config", "analysis.strict-equality-semantics=true"),
    ("--config", "analysis.strict-equality-semantics=false"),
    ("--config", "analysis.strict-generic-narrowing=true"),
    ("--config", "analysis.strict-generic-narrowing=false"),
}
_TY_RULE_FLAG = re.compile(r"^--(error|warn|ignore)$")
_RULE_NAME = re.compile(r"^[a-z][a-z0-9-]*$")
ALLOWED_MYPY_FLAGS = {
    "--strict", "--strict-equality", "--warn-unreachable", "--no-implicit-reexport", "--extra-checks",
    "--no-check-untyped-defs", "--check-untyped-defs", "--local-partial-types", "--allow-redefinition",
    "--allow-redefinition-new", "--strict-bytes", "--warn-return-any", "--disallow-any-generics",
    "--warn-redundant-casts", "--warn-unused-ignores", "--disallow-untyped-defs", "--disallow-untyped-calls",
    "--disallow-untyped-decorators", "--implicit-optional", "--no-strict-optional",
}
_MYPY_CODE_FLAG = re.compile(r"^--(enable|disable)-error-code$")
MYPY_CODE_ENABLERS = {
    "unreachable": ["--warn-unreachable"], "comparison-overlap": ["--strict-equality"],
    "redundant-cast": ["--warn-redundant-casts"], "no-any-return": ["--warn-return-any"],
    "unused-ignore": ["--warn-unused-ignores"], "no-untyped-def": ["--disallow-untyped-defs"],
    "no-untyped-call": ["--disallow-untyped-calls"], "untyped-decorator": ["--disallow-untyped-decorators"],
}
# documented opt-in soundness checks (mypy: error_code_list2 / command_line; ty: rules with default level "ignore")
OPT_IN_FLAGS = {
    Tool.MYPY: ["--enable-error-code", "mutable-override", "--enable-error-code", "possibly-undefined",
                "--enable-error-code", "redundant-expr", "--strict-equality", "--warn-unreachable", "--extra-checks"],
    Tool.TY: ["--error", "unsound-assignment", "--error", "unsound-return-statement", "--error", "unsound-yield",
              "--error", "possibly-unresolved-reference", "--error", "possibly-missing-attribute",
              "--config", "analysis.strict-equality-semantics=true", "--config", "analysis.strict-generic-narrowing=true"],
}
# new errors from these families are *expected* after replacing an annotation with Any
_GRADUAL_EXEMPT = {"assert-type", "type-assertion-failure", "redundant-cast", "unused-ignore", "unused-ignore-comment",
                   "unused-type-ignore-comment", "no-any-return", "unsound-return-statement", "unsound-assignment",
                   "unsound-yield", "overload-overlap", "redundant-condition", "truthy-bool"}
_QUALIFIERS = {"ClassVar", "Final", "InitVar", "Required", "NotRequired", "ReadOnly", "Annotated", "TypeAlias",
               "TypeGuard", "TypeIs", "Unpack", "Self", "Never", "NoReturn"}
_PEP585 = {"List": "list", "Dict": "dict", "Set": "set", "FrozenSet": "frozenset", "Tuple": "tuple", "Type": "type"}


@dataclass
class ExperimentResult:
    id: str
    kind: str
    request: dict[str, Any]
    ok: bool
    summary: str
    outcome: dict[str, Any] = field(default_factory=dict)
    evidence: Evidence | None = None
    discrepancy_id: str = ""


class ExperimentError(ValueError):
    pass


# --------------------------------------------------------------------------- helpers


def _problem_map(diags: list[Diagnostic], amap: AnchorMap) -> dict[str, set[str]]:
    """statement path -> {code} of problem diagnostics (for metamorphic comparison)."""
    out: dict[str, set[str]] = {}
    for d in diags:
        if not d.is_problem or (d.code or "") in META_CODES:
            continue
        p = amap.path(d.line) or f"line{d.line}"
        out.setdefault(p, set()).add(d.code or "?")
    return out


def _insert_lines(source: str, before_line: int, new_lines: list[str]) -> str:
    lines = source.splitlines()
    indent = re.match(r"\s*", lines[before_line - 1]).group(0)
    lines[before_line - 1:before_line - 1] = [indent + nl for nl in new_lines]
    return "\n".join(lines) + "\n"


def _annotation_slots(tree: ast.Module) -> list[tuple[ast.AST, str]]:
    """(owner node, attribute name) pairs for every annotation position."""
    slots: list[tuple[ast.AST, str]] = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if n.returns is not None:
                slots.append((n, "returns"))
            for a in [*n.args.posonlyargs, *n.args.args, *n.args.kwonlyargs, n.args.vararg, n.args.kwarg]:
                if a is not None and a.annotation is not None:
                    slots.append((a, "annotation"))
        elif isinstance(n, ast.AnnAssign):
            slots.append((n, "annotation"))
    return slots


def _typevar_names(tree: ast.Module) -> set[str]:
    names = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call):
            fn = n.value.func
            fname = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", "")
            if fname in ("TypeVar", "ParamSpec", "TypeVarTuple"):
                names.update(t.id for t in n.targets if isinstance(t, ast.Name))
        for p in getattr(n, "type_params", []) or []:
            names.add(p.name)
    return names


def _mentions(node: ast.AST, names: set[str]) -> bool:
    return any(isinstance(x, ast.Name) and x.id in names for x in ast.walk(node))


def _is_overload(fn: ast.AST) -> bool:
    return any((isinstance(d, ast.Name) and d.id == "overload") or (isinstance(d, ast.Attribute) and d.attr == "overload")
               for d in getattr(fn, "decorator_list", []))


class _Rewrite(ast.NodeTransformer):
    """PEP 604 / PEP 585 rewrites restricted to annotation subtrees without string forward refs."""

    def __init__(self, mode: str):
        self.mode = mode
        self.changed = 0

    def rewrite(self, ann: ast.AST) -> ast.AST:
        if any(isinstance(x, ast.Constant) and isinstance(x.value, str) for x in ast.walk(ann)):
            return ann
        return self.visit(ann)

    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
        self.generic_visit(node)
        base = node.value.id if isinstance(node.value, ast.Name) else (node.value.attr if isinstance(node.value, ast.Attribute) else None)
        if self.mode == "pep604" and base in ("Optional", "Union"):
            members = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
            if base == "Optional":
                members = [members[0], ast.Constant(None)]
            expr = members[0]
            for m in members[1:]:
                expr = ast.BinOp(left=expr, op=ast.BitOr(), right=m)
            self.changed += 1
            return expr
        if self.mode == "pep585" and base in _PEP585:
            self.changed += 1
            return ast.Subscript(value=ast.Name(_PEP585[base], ast.Load()), slice=node.slice, ctx=node.ctx)
        return node


# --------------------------------------------------------------------------- runner


class ExperimentRunner:
    def __init__(self, state: "CaseState"):
        self.s = state
        self.counter = 0
        self.results: list[ExperimentResult] = []

    def _id(self) -> str:
        self.counter += 1
        return f"E{self.counter}"

    @property
    def online(self) -> bool:
        return self.s.runners is not None

    def run(self, d: Discrepancy, req: dict[str, Any]) -> ExperimentResult:
        kind = req.get("kind", "")
        try:
            if not self.online and kind != "request_context":
                raise ExperimentError("offline mode: tools cannot be re-run")
            fn = {
                "config_toggle": self.config_toggle, "reveal_probe": self.reveal_probe, "metamorphic": self.metamorphic,
                "variant": self.variant, "witness": self.witness, "pyright": self.pyright,
                "opt_in_checks": self.opt_in_checks, "assignability": self.assignability,
            }.get(kind)
            if fn is None:
                raise ExperimentError(f"unknown/unsupported experiment kind {kind!r}")
            res = fn(d, req)
        except ExperimentError as exc:
            res = ExperimentResult(self._id(), kind, req, False, f"rejected: {exc}")
        except Exception as exc:  # noqa: BLE001 - experiments must never crash the pipeline
            res = ExperimentResult(self._id(), kind, req, False, f"error: {type(exc).__name__}: {exc}")
        res.discrepancy_id = d.id
        self.results.append(res)
        return res

    def for_discrepancy(self, d_id: str) -> list[ExperimentResult]:
        return [r for r in self.results if r.discrepancy_id == d_id]

    # ------------------------------------------------------------------ persistence check
    def discrepancy_persists(self, d: Discrepancy, diags: dict[Tool, list[Diagnostic]], source: str | None = None) -> bool:
        src = source or self.s.source
        amap = AnchorMap(src) if source else self.s.amap
        new = find_discrepancies({k: [copy.copy(x) for x in v] for k, v in diags.items()}, amap, self.s.runtime, self.s.module)
        for nd in new:
            if nd.anchor != d.anchor:
                continue
            if nd.kind == d.kind == DiscrepancyKind.ONLY_MYPY and {x.code for x in nd.mypy} & {x.code for x in d.mypy}:
                return True
            if nd.kind == d.kind == DiscrepancyKind.ONLY_TY and {x.code for x in nd.ty} & {x.code for x in d.ty}:
                return True
            if nd.kind == d.kind and d.kind not in (DiscrepancyKind.ONLY_MYPY, DiscrepancyKind.ONLY_TY):
                return True
        return False

    # ------------------------------------------------------------------ kinds
    def config_toggle(self, d: Discrepancy, req: dict[str, Any]) -> ExperimentResult:
        tool = Tool(req.get("tool", ""))
        flags = [str(f) for f in req.get("flags", [])]
        self._validate_flags(tool, flags)
        res = self.s.runners.check(tool, self.s.source, flags)
        diags = {k: list(v) for k, v in self.s.diags.items()}
        diags[tool] = res.diagnostics
        persists = self.discrepancy_persists(d, diags)
        at_anchor = [x.short() for x in res.diagnostics if self.s.amap.anchor(x.line) == d.anchor]
        summary = f"{tool.value} {' '.join(flags)} -> discrepancy {'PERSISTS' if persists else 'DISAPPEARS'}"
        ev = Evidence(
            EvidenceType.EXPERIMENT, "neutral" if persists else "not_bug", summary, citation="", verified=True,
            strength="medium",
        )
        return ExperimentResult(self._id(), "config_toggle", req, True, summary,
                                {"persists": persists, "diagnostics_at_statement": at_anchor,
                                 "crashed": [c.signature for c in res.crashes]}, ev)

    def _validate_flags(self, tool: Tool, flags: list[str]) -> None:
        i = 0
        while i < len(flags):
            f = flags[i]
            nxt = flags[i + 1] if i + 1 < len(flags) else None
            if f == "--python-version" and nxt and re.fullmatch(r"3\.\d{1,2}", nxt):
                i += 2
                continue
            if tool == Tool.TY:
                if (f, nxt) in ALLOWED_TY_FLAGS or (_TY_RULE_FLAG.match(f) and nxt and _RULE_NAME.match(nxt)):
                    i += 2
                    continue
            if tool == Tool.MYPY:
                if f in ALLOWED_MYPY_FLAGS:
                    i += 1
                    continue
                if _MYPY_CODE_FLAG.match(f) and nxt and _RULE_NAME.match(nxt):
                    i += 2
                    continue
            raise ExperimentError(f"flag {f!r} not in allow-list for {tool.value}")

    def reveal_probe(self, d: Discrepancy, req: dict[str, Any]) -> ExperimentResult:
        line = int(req.get("line") or d.anchor)
        st = self.s.amap.stmt(line)
        if st is None or not st.insertable:
            raise ExperimentError(f"cannot insert a probe before line {line} (not a plain statement)")
        exprs = [e for e in req.get("exprs", []) if isinstance(e, str)][:8]
        for e in exprs:
            try:
                node = ast.parse(e, mode="eval").body
            except SyntaxError as exc:
                raise ExperimentError(f"probe {e!r} is not an expression") from exc
            if any(isinstance(x, (ast.Call, ast.NamedExpr, ast.Await, ast.Yield, ast.Lambda)) for x in ast.walk(node)):
                raise ExperimentError(f"probe {e!r} has side effects; only names/attributes/subscripts allowed")
        if not exprs:
            raise ExperimentError("no expressions to probe")
        memo = getattr(self, "_probe_memo", None)
        if memo is None:
            memo = self._probe_memo = {}
        key = (st.anchor, tuple(exprs))
        if key in memo:  # identical probe already run (e.g. auto-probe, then the call oracle)
            prev = memo[key]
            return ExperimentResult(self._id(), "reveal_probe", req, True, prev.summary + f" (cached {prev.id})",
                                    copy.deepcopy(prev.outcome))
        at = st.anchor
        src = _insert_lines(self.s.source, at, [f"reveal_type({e})" for e in exprs])
        probe_lines = {at + i: e for i, e in enumerate(exprs)}
        outcome: dict[str, dict[str, Any]] = {e: {} for e in exprs}
        tools = [Tool.MYPY, Tool.TY] + ([Tool.PYRIGHT] if self.s.use_pyright else [])
        for tool in tools:
            r = self.s.runners.check(tool, src)
            for x in r.diagnostics:
                if x.revealed_type is not None and x.line in probe_lines:
                    outcome[probe_lines[x.line]][tool.value] = x.revealed_type
        rt = self.s.runners.run_runtime(src)
        for p in rt.probes:
            if p.line in probe_lines:
                outcome[probe_lines[p.line]].setdefault("runtime", p.shape.get("type"))
                outcome[probe_lines[p.line]].setdefault("_shape", p.shape)
        lines = []
        for e, o in outcome.items():
            m, t = normalize(o.get("mypy"), self.s.module), normalize(o.get("ty"), self.s.module)
            rel = rel_name(relation(m, t)) if m and t else "missing"
            o["relation"] = rel
            shape = o.pop("_shape", None)
            if shape is not None:
                o["runtime_in_mypy_type"] = inhabits(shape, m, self.s.nominal_classes) if m else None
                o["runtime_in_ty_type"] = inhabits(shape, t, self.s.nominal_classes) if t else None
            lines.append(f"{e}: mypy={o.get('mypy')} ty={o.get('ty')} pyright={o.get('pyright')} "
                         f"runtime={o.get('runtime')} [{rel}]")
        res = ExperimentResult(self._id(), "reveal_probe", req, True, "; ".join(lines), outcome)
        memo[key] = res
        return res

    def metamorphic(self, d: Discrepancy, req: dict[str, Any]) -> ExperimentResult:
        transform = req.get("transform")
        if transform in ("pep604", "pep585"):
            return self._syntactic_equivalence(d, req, transform)
        if transform == "any_substitution":
            return self._gradual_guarantee(d, req)
        raise ExperimentError(f"unknown transform {transform!r}")

    def _baseline_maps(self) -> dict[Tool, dict[str, set[str]]]:
        """Diagnostics of the *identity* round-trip ``ast.unparse(ast.parse(src))``.

        Comparing a rewritten program against the unparsed original (not the raw file) makes sure
        that formatting/comment loss caused by unparse can never masquerade as a self-contradiction.
        """
        if getattr(self, "_baseline", None) is None:
            src = ast.unparse(ast.parse(self.s.source)) + "\n"
            amap = AnchorMap(src)
            self._baseline = {t: _problem_map(self.s.runners.check(t, src).diagnostics, amap) for t in (Tool.MYPY, Tool.TY)}
        return self._baseline

    def _syntactic_equivalence(self, d: Discrepancy, req: dict, transform: str) -> ExperimentResult:
        tree = ast.parse(self.s.source)
        rw = _Rewrite(transform)
        for owner, attr in _annotation_slots(tree):
            setattr(owner, attr, rw.rewrite(getattr(owner, attr)))
        if not rw.changed:
            raise ExperimentError(f"{transform}: nothing to rewrite")
        ast.fix_missing_locations(tree)
        src = ast.unparse(tree) + "\n"
        vmap = AnchorMap(src)
        base = self._baseline_maps()
        changed: dict[str, Any] = {}
        for tool in (Tool.MYPY, Tool.TY):
            r = self.s.runners.check(tool, src)
            after = _problem_map(r.diagnostics, vmap)
            if after != base[tool]:
                changed[tool.value] = {"before": {k: sorted(v) for k, v in base[tool].items()},
                                       "after": {k: sorted(v) for k, v in after.items()}}
        ev = None
        if changed:
            blamed = ",".join(changed)
            ev = Evidence(EvidenceType.SELF_CONTRADICTION, "bug",
                          f"{blamed} gives different diagnostics after a spec-equivalent {transform} rewrite "
                          f"({rw.changed} annotations rewritten)", citation="", verified=True, strength="strong",
                          blame=blamed)
        summary = f"{transform} rewrite ({rw.changed} sites): " + ("results CHANGED for " + ", ".join(changed) if changed else "results identical")
        return ExperimentResult(self._id(), "metamorphic", req, True, summary,
                                {"changed": changed, "variant_source": src}, ev)

    def _gradual_guarantee(self, d: Discrepancy, req: dict) -> ExperimentResult:
        """Replace ONE annotation at a time with Any; a sound gradual checker must not report *new* errors."""
        tree = ast.parse(self.s.source)
        tvars = _typevar_names(tree)
        bound_any = any(isinstance(n, ast.ImportFrom) and n.module in ("typing", "typing_extensions")
                        and any(a.name == "Any" and not a.asname for a in n.names) for n in tree.body)
        target = req.get("target")
        slots = []
        parents = {id(c): p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}
        for owner, attr in _annotation_slots(tree):
            ann = getattr(owner, attr)
            if isinstance(ann, ast.Constant) or _mentions(ann, tvars) or _mentions(ann, _QUALIFIERS):
                continue
            fn = owner if isinstance(owner, (ast.FunctionDef, ast.AsyncFunctionDef)) else parents.get(id(parents.get(id(owner))))
            if fn is not None and _is_overload(fn):
                continue
            if target and target not in (ast.unparse(ann), getattr(owner, "arg", None),
                                         getattr(getattr(owner, "target", None), "id", None)):
                continue
            slots.append((owner, attr))
        # prefer annotations near the discrepancy
        slots.sort(key=lambda s: abs(getattr(s[0], "lineno", 10**6) - d.anchor))
        slots = slots[: int(req.get("max_variants", 5))]
        if not slots:
            raise ExperimentError("no substitutable annotation (qualifiers/TypeVars/overloads are excluded)")
        base = self._baseline_maps()
        violations: list[dict[str, Any]] = []
        for owner, attr in slots:
            vtree = ast.parse(self.s.source)
            # locate the same slot in the fresh tree by position
            lineno, col = getattr(owner, "lineno", None), getattr(owner, "col_offset", None)
            for vo, va in _annotation_slots(vtree):
                if va == attr and getattr(vo, "lineno", None) == lineno and getattr(vo, "col_offset", None) == col:
                    original = ast.unparse(getattr(vo, va))
                    setattr(vo, va, ast.Name("Any", ast.Load()))
                    break
            else:
                continue
            insert_at = 0
            if not bound_any:
                while insert_at < len(vtree.body) and (
                    (isinstance(vtree.body[insert_at], ast.ImportFrom) and vtree.body[insert_at].module == "__future__")
                    or (insert_at == 0 and isinstance(vtree.body[0], ast.Expr) and isinstance(getattr(vtree.body[0], "value", None), ast.Constant))
                ):
                    insert_at += 1
                vtree.body.insert(insert_at, ast.ImportFrom("typing", [ast.alias("Any")], 0))
            ast.fix_missing_locations(vtree)
            src = ast.unparse(vtree) + "\n"
            vmap = AnchorMap(src)
            for tool in (Tool.MYPY, Tool.TY):
                r = self.s.runners.check(tool, src)
                after = _problem_map(r.diagnostics, vmap)
                if not bound_any:
                    after = _unshift_paths(after, insert_at)
                for path, codes in after.items():
                    new_codes = {c for c in codes - base[tool].get(path, set()) if c not in _GRADUAL_EXEMPT}
                    if new_codes:
                        violations.append({"tool": tool.value, "annotation": original, "line": lineno, "path": path,
                                           "new_codes": sorted(new_codes)})
        ev = None
        if violations:
            blamed = ",".join(sorted({v["tool"] for v in violations}))
            ev = Evidence(EvidenceType.SELF_CONTRADICTION, "bug",
                          f"gradual-guarantee violation: replacing an annotation with Any introduced new errors in {blamed}",
                          citation="", verified=True, strength="strong", blame=blamed)
        summary = f"any_substitution over {len(slots)} annotation(s): " + (f"{len(violations)} NEW error(s) introduced" if violations else "no new errors")
        return ExperimentResult(self._id(), "metamorphic", req, True, summary, {"violations": violations}, ev)

    def variant(self, d: Discrepancy, req: dict[str, Any]) -> ExperimentResult:
        src = req.get("source", "")
        if not isinstance(src, str) or not src.strip():
            raise ExperimentError("variant needs 'source'")
        if len(src) > 20000:
            raise ExperimentError("variant too large")
        ast.parse(src)
        outcome = self._full_run(src)
        outcome["relation_claimed"] = req.get("relation", "")
        summary = (f"variant: mypy={len(outcome['mypy'])} problems, ty={len(outcome['ty'])} problems, "
                   f"runtime={outcome['runtime']}")
        ev = Evidence(EvidenceType.EXPERIMENT, "neutral", summary + f" (claimed relation: {req.get('relation', '')})",
                      verified=False, strength="medium")
        return ExperimentResult(self._id(), "variant", req, True, summary, outcome, ev)

    def witness(self, d: Discrepancy, req: dict[str, Any]) -> ExperimentResult:
        extra = req.get("append", "")
        if not isinstance(extra, str) or not extra.strip() or len(extra) > 5000:
            raise ExperimentError("witness needs a short 'append' snippet")
        base = self.s.source
        dropped = False
        if self.s.runtime.status == "exception":
            # the original program dies before an appended witness could run: keep definitions only
            base, dropped = _definitions_only(self.s.source), True
        src = base.rstrip("\n") + "\n\n# --- witness (typediff) ---\n" + extra.rstrip("\n") + "\n"
        ast.parse(src)
        first_witness_line = len(base.rstrip("\n").splitlines()) + 3
        outcome = self._full_run(src)
        rt = outcome.pop("_runtime_obj")
        in_witness = any(ln >= first_witness_line for ln, _ in rt.frames)
        strong = rt.status == "exception" and classify_exception(rt.exc_type, rt.exc_message) == "strong" and in_witness
        silent = [t for t in ("mypy", "ty")
                  if not any(int(re.match(r"L(\d+)", s).group(1)) >= first_witness_line for s in outcome[t])]
        outcome["definitions_only"] = dropped
        ev = None
        if strong and silent:
            ev = Evidence(EvidenceType.RUNTIME, "bug",
                          f"witness program accepted by {', '.join(silent)} raises {rt.exc_type}: {rt.exc_message} "
                          f"at line {rt.exc_line}", citation=f"witness from line {first_witness_line}", verified=True,
                          strength="strong", blame=",".join(silent))
        summary = f"witness: runtime={rt.status} {rt.exc_type or ''}; silent checkers: {silent or 'none'}"
        outcome["witness_source"] = src
        return ExperimentResult(self._id(), "witness", req, True, summary, outcome, ev)

    def assignability(self, d: Discrepancy, req: dict[str, Any]) -> ExperimentResult:
        """Ask checkers whether ``expr`` is assignable to ``type`` via ``_td_probe: <type> = <expr>`` inserted
        right before the statement (static only; the variant is never executed)."""
        typ, expr = str(req.get("type", "")), str(req.get("expr", ""))
        try:
            ast.parse(typ, mode="eval")
            ast.parse(expr, mode="eval")
        except SyntaxError as exc:
            raise ExperimentError("type/expr must be Python expressions") from exc
        if len(typ) > 300 or len(expr) > 300:
            raise ExperimentError("type/expr too long")
        st = self.s.amap.stmt(int(req.get("line") or d.anchor))
        if st is None or not st.insertable:
            raise ExperimentError("cannot insert before this statement")
        src = _insert_lines(self.s.source, st.anchor, [f"_td_probe: {typ} = {expr}"])
        outcome: dict[str, Any] = {}
        tools = [Tool(t) for t in req.get("tools", ["mypy", "ty"])]
        for tool in tools:
            r = self.s.runners.check(tool, src)
            outcome[tool.value] = [x.short() for x in r.diagnostics
                                   if x.line == st.anchor and x.is_problem and (x.code or "") not in META_CODES]
        summary = "; ".join(f"{t}: {'REJECTS' if v else 'accepts'} `_td_probe: {typ} = {expr}`" for t, v in outcome.items())
        return ExperimentResult(self._id(), "assignability", req, True, summary, outcome,
                                Evidence(EvidenceType.EXPERIMENT, "neutral", summary, verified=True, strength="medium"))

    def opt_in_checks(self, d: Discrepancy, req: dict[str, Any]) -> ExperimentResult:
        """Re-run both checkers with their documented *opt-in* soundness checks and list what they add.

        Answers: "is this runtime failure caught by a check the tool deliberately keeps off by default?"
        (documented design / known limitation) vs "no mode of this tool catches it" (stronger bug signal).
        """
        lines_of_interest = {self.s.amap.anchor(ln) for ln, _ in self.s.runtime.frames} | {d.anchor}
        found: dict[str, list[str]] = {}
        for tool, flags in OPT_IN_FLAGS.items():
            r = self.s.runners.check(tool, self.s.source, flags)
            base = {(x.line, x.code) for x in self.s.diags.get(tool, []) if x.is_problem}
            new = [x for x in r.diagnostics if x.is_problem and (x.line, x.code) not in base
                   and (x.code or "") not in META_CODES]
            found[tool.value] = [x.short() + ("  <-- on traceback/anchor statement" if self.s.amap.anchor(x.line) in lines_of_interest else "")
                                 for x in new]
        summary = "; ".join(f"{t}: {len(v)} new ({', '.join(sorted({s.split(']')[0].split('[')[-1] for s in v if '[' in s}))})"
                            for t, v in found.items())
        ev = Evidence(EvidenceType.EXPERIMENT, "neutral", f"opt-in soundness checks -> {summary}", verified=True,
                      strength="medium")
        return ExperimentResult(self._id(), "opt_in_checks", req, True, summary, found, ev)

    def pyright(self, d: Discrepancy, req: dict[str, Any]) -> ExperimentResult:
        at = [x.short() for x in self.s.diags.get(Tool.PYRIGHT, []) if self.s.amap.anchor(x.line) == d.anchor]
        if not self.s.pyright_ran:
            raise ExperimentError("pyright not available")
        side = _pyright_side(d, self.s.diags.get(Tool.PYRIGHT, []), self.s.amap)
        ev = Evidence(EvidenceType.CONSENSUS, "neutral", f"pyright at this statement: {at or 'silent'}; sides with {side}",
                      verified=True, strength="weak")
        return ExperimentResult(self._id(), "pyright", req, True, ev.summary, {"pyright": at, "sides_with": side}, ev)

    def _full_run(self, src: str) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for tool in (Tool.MYPY, Tool.TY):
            r = self.s.runners.check(tool, src)
            out[tool.value] = [x.short() for x in r.diagnostics if x.is_problem and (x.code or "") not in META_CODES]
            out[tool.value + "_reveals"] = [x.short() for x in r.diagnostics if x.revealed_type is not None]
            out[tool.value + "_crashes"] = [c.signature for c in r.crashes]
        rt = self.s.runners.run_runtime(src)
        out["runtime"] = f"{rt.status} {rt.exc_type or ''} {rt.exc_message or ''} line={rt.exc_line}".strip()
        out["_runtime_obj"] = rt
        return out


_DEF_NODES = (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Assign, ast.AnnAssign)


def _definitions_only(source: str) -> str:
    """Keep imports/defs/classes/assignments of literal-ish values; drop module-level 'driver' code."""
    tree = ast.parse(source)
    keep = []
    for n in tree.body:
        if isinstance(n, _DEF_NODES[:5]) or (hasattr(ast, "TypeAlias") and isinstance(n, ast.TypeAlias)):
            keep.append(n)
        elif isinstance(n, (ast.Assign, ast.AnnAssign)) and not any(isinstance(x, ast.Call) for x in ast.walk(n)):
            keep.append(n)
        elif isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) and getattr(n.value.func, "id", "") in (
                "TypeVar", "ParamSpec", "TypeVarTuple", "NewType", "NamedTuple", "TypedDict"):
            keep.append(n)
    tree.body = keep or [ast.Pass()]
    return ast.unparse(tree) + "\n"


def _unshift_paths(m: dict[str, set[str]], insert_at: int) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for path, codes in m.items():
        mm = re.match(r"^body\[(\d+)\](.*)$", path)
        if mm:
            k = int(mm.group(1))
            if k == insert_at:
                continue  # the inserted import itself
            if k > insert_at:
                path = f"body[{k - 1}]{mm.group(2)}"
        out[path] = codes
    return out


def _pyright_side(d: Discrepancy, pyright: list[Diagnostic], amap: AnchorMap) -> str:
    probs = [x for x in pyright if x.is_problem and amap.anchor(x.line) == d.anchor]
    if d.kind == DiscrepancyKind.ONLY_MYPY:
        return "mypy" if probs else "ty"
    if d.kind == DiscrepancyKind.ONLY_TY:
        return "ty" if probs else "mypy"
    if d.kind == DiscrepancyKind.REVEAL_MISMATCH:
        revs = [x for x in pyright if x.revealed_type is not None and amap.anchor(x.line) == d.anchor]
        if revs and d.mypy and d.ty:
            p = normalize(revs[0].revealed_type)
            if relation(p, normalize(d.ty[0].revealed_type)) in (Relation.EQUAL, Relation.COSMETIC):
                return "ty"
            if relation(p, normalize(d.mypy[0].revealed_type)) in (Relation.EQUAL, Relation.COSMETIC):
                return "mypy"
        return "neither"
    return "n/a"


def default_probe_exprs(state: "CaseState", d: Discrepancy, limit: int = 6) -> list[str]:
    """Pick side-effect-free operands of the statement whose types explain the discrepancy."""
    st = state.amap.stmt(d.anchor)
    if st is None or st.node is None:
        return []
    node = st.node
    roots: list[ast.AST]
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return []
    roots = [node.test] if isinstance(node, (ast.If, ast.While)) else (
        [node.iter] if isinstance(node, (ast.For, ast.AsyncFor)) else [node])
    bound_here = {n.id for r in roots for n in ast.walk(r) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    for r in roots:  # comprehension / lambda variables are not in scope before the statement
        for n in ast.walk(r):
            if isinstance(n, ast.comprehension):
                bound_here |= {x.id for x in ast.walk(n.target) if isinstance(x, ast.Name)}
            if isinstance(n, ast.Lambda):
                bound_here |= {a.arg for a in n.args.args}
    defs = state.defined_callables
    seen: list[str] = []
    for r in roots:
        for n in ast.walk(r):
            expr = None
            if isinstance(n, ast.Attribute) and isinstance(n.ctx, ast.Load) and isinstance(n.value, ast.Name):
                if n.value.id not in bound_here and n.value.id not in defs:
                    expr = f"{n.value.id}.{n.attr}"
            elif isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                if n.id not in bound_here and n.id not in defs and n.id not in state.builtin_names:
                    expr = n.id
            if expr and expr not in seen:
                seen.append(expr)
    return seen[:limit]


def family_of(d: Diagnostic) -> str | None:
    return family(d.code)


# --------------------------------------------------------------------------- call/assignability consistency oracle

_MYPY_ARG = re.compile(r'has incompatible type "(?P<found>.+)"; expected "(?P<expected>.+)"$')
_TY_ARG = re.compile(r"Expected `(?P<expected>.+?)`, found `(?P<found>.+?)`")


def _split_params(sig: str) -> list[str]:
    """Top-level parameters of a canonical '(a: int, *, b: str=) -> R' signature."""
    if not sig.startswith("("):
        return []
    depth, cur, out = 0, "", []
    for ch in sig[1:]:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            if depth == 0:
                if cur.strip():
                    out.append(cur.strip())
                return out
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
            continue
        cur += ch
    return out


def _param_type(sig_text: str, index: int | None, name: str | None) -> str | None:
    params = [p for p in _split_params(sig_text) if p not in ("*", "/")]
    chosen = None
    if name:
        chosen = next((p for p in params if p.split(":", 1)[0].strip().lstrip("*") == name), None)
    elif index is not None:
        positional = [p for p in params if not p.startswith("*")]
        chosen = positional[index] if index < len(positional) else None
    if not chosen or ":" not in chosen:
        return None
    return chosen.split(":", 1)[1].rstrip("=").strip()


def call_assignability_oracle(state: "CaseState", d: Discrepancy, ex: ExperimentRunner) -> Evidence | None:
    """ONLY_MYPY arg-type / ONLY_TY invalid-argument-type: does the *silent* checker contradict itself?

    1. locate the argument the reporting checker points at (by column) and its parameter slot;
    2. reveal the callee in the silent checker and read that parameter's type from ITS signature;
    3. ask the silent checker whether ``_td_probe: <that type> = <argument>`` is OK.
    If it rejects the assignment yet accepted the call, it is inconsistent with itself -> SELF_CONTRADICTION.
    """
    if d.kind == DiscrepancyKind.ONLY_MYPY:
        reporter, silent = [x for x in d.mypy if x.code == "arg-type"], Tool.TY
    elif d.kind == DiscrepancyKind.ONLY_TY:
        reporter, silent = [x for x in d.ty if x.code == "invalid-argument-type"], Tool.MYPY
    else:
        return None
    st = state.amap.stmt(d.anchor)
    if not reporter or st is None or st.node is None or not st.insertable:
        return None
    diag = reporter[0]
    target = None
    for call in (n for n in ast.walk(st.node) if isinstance(n, ast.Call)):
        for i, a in enumerate(call.args):
            if (a.lineno, a.col_offset + 1) == (diag.line, diag.col) and not isinstance(a, ast.Starred):
                target = (call, a, i, None)
        for kw in call.keywords:
            if kw.arg and (kw.value.lineno, kw.value.col_offset + 1) == (diag.line, diag.col):
                target = (call, kw.value, None, kw.arg)
    if target is None:
        return None
    call, arg, idx, kwname = target
    if any(isinstance(x, (ast.Call, ast.NamedExpr, ast.Await, ast.Lambda)) for x in ast.walk(call.func)):
        return None
    callee = ast.unparse(call.func)
    cached = (state.probe_cache.get(d.id) or {}).get(callee, {})
    if cached.get(silent.value):
        sig, probe_id = cached[silent.value], "auto-probe"
    else:
        probe = ex.run(d, {"kind": "reveal_probe", "line": d.anchor, "exprs": [callee]})
        sig = probe.outcome.get(callee, {}).get(silent.value) if probe.ok else None
        probe_id = probe.id
    norm = normalize(sig, state.module) if sig else None
    ptype = _param_type(norm.text, idx, kwname) if norm else None
    if not ptype or "Unknown" in ptype or "Any" in ptype:
        return None
    res = ex.run(d, {"kind": "assignability", "type": ptype, "expr": ast.unparse(arg), "tools": [silent.value]})
    rejections = res.outcome.get(silent.value, []) if res.ok else []
    # only a genuine assignability rejection counts (not e.g. an unresolved name in the probe line)
    if not any(re.search(r"\[(assignment|invalid-assignment)\]", r) for r in rejections):
        return None
    return Evidence(
        EvidenceType.SELF_CONTRADICTION, "bug",
        f"{silent.value} reveals `{callee}` as `{norm.text}` (parameter type `{ptype}`), rejects "
        f"`_td_probe: {ptype} = {ast.unparse(arg)}` ({rejections[0]}), yet accepts the call "
        f"({probe_id}, {res.id})", citation=res.id, verified=True, strength="strong", blame=silent.value)
