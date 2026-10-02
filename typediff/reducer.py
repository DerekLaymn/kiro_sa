"""Hierarchical delta debugging (statement-level ddmin over the AST) that preserves a
discrepancy *signature*. Produces the minimal repro that goes into the upstream report and the
dedup signature that goes into the dataset."""

from __future__ import annotations

import ast
from typing import Callable

from .anchors import AnchorMap, statement_key
from .concerns import same_concern
from .discrepancy import META_CODES
from .models import Discrepancy, DiscrepancyKind, EvidenceType, Finding, Tool
from .parsers import classify_exception
from .runners import Runners
from .typenorm import normalize, relation

K = DiscrepancyKind
_NEEDS_BODY = {"body"}


class Reducer:
    def __init__(self, runners: Runners, module: str = "case", max_tests: int = 250):
        self.runners = runners
        self.module = module
        self.max_tests = max_tests
        self.tests = 0

    # ------------------------------------------------------------------ predicates
    def predicate_for(self, source: str, d: Discrepancy | None, finding: Finding, crash_signature: str | None = None,
                      crash_tool: Tool | None = None) -> Callable[[str], bool]:
        if crash_signature and crash_tool:
            def crash_pred(src: str) -> bool:
                r = self.runners.check(crash_tool, src)
                return any(c.signature == crash_signature for c in r.crashes)
            return crash_pred

        assert d is not None
        amap = AnchorMap(source)
        st = amap.stmt(d.anchor)
        key = statement_key(st.node) if st and st.node is not None else d.statement
        need_runtime = any(e.type == EvidenceType.RUNTIME and e.supports == "bug" and e.verified for e in finding.evidence)
        m_codes = {x.code for x in d.mypy}
        t_codes = {x.code for x in d.ty}
        orig_rel = d.reveal_relation
        # errors elsewhere must not grow: a repro that only works because it is broken elsewhere is useless upstream
        baseline: dict[Tool, set[str]] = {}
        for tool in (Tool.MYPY, Tool.TY):
            r0 = self.runners.check(tool, source)
            baseline[tool] = {x.code or "" for x in r0.diagnostics
                              if x.is_problem and amap.anchor(x.line) != d.anchor and (x.code or "") not in META_CODES}

        def clean_elsewhere(diags, vm, anchor, tool) -> bool:
            other = [x for x in diags if x.is_problem and vm.anchor(x.line) != anchor and (x.code or "") not in META_CODES]
            return {x.code or "" for x in other} <= baseline[tool]

        def pred(src: str) -> bool:
            vm = AnchorMap(src)
            if vm.syntax_error:
                return False
            cands = [s for s in vm.statements if s.node is not None and _safe_key(s.node) == key]
            if not cands:
                return False
            mypy = self.runners.check(Tool.MYPY, src)
            ty = self.runners.check(Tool.TY, src)
            if mypy.crashes or ty.crashes:
                return False
            for s in cands:
                if not (clean_elsewhere(mypy.diagnostics, vm, s.anchor, Tool.MYPY)
                        and clean_elsewhere(ty.diagnostics, vm, s.anchor, Tool.TY)):
                    continue
                m = [x for x in mypy.diagnostics if vm.anchor(x.line) == s.anchor]
                t = [x for x in ty.diagnostics if vm.anchor(x.line) == s.anchor]
                mp = [x for x in m if x.is_problem and (x.code or "") not in META_CODES]
                tp = [x for x in t if x.is_problem and (x.code or "") not in META_CODES]
                ok = False
                if d.kind == K.ONLY_MYPY:
                    hit = [x for x in mp if x.code in m_codes]
                    ok = bool(hit) and not any(same_concern(a, b) for a in hit for b in tp)
                elif d.kind == K.ONLY_TY:
                    hit = [x for x in tp if x.code in t_codes]
                    ok = bool(hit) and not any(same_concern(a, b) for a in hit for b in mp)
                elif d.kind == K.CONCERN_MISMATCH:
                    ok = bool(mp) and bool(tp) and not any(same_concern(a, b) for a in mp for b in tp)
                elif d.kind == K.REVEAL_MISMATCH:
                    rm = [x for x in m if x.revealed_type is not None]
                    rt_ = [x for x in t if x.revealed_type is not None]
                    if rm and rt_:
                        from .discrepancy import rel_name
                        rel = rel_name(relation(normalize(rm[0].revealed_type, self.module), normalize(rt_[0].revealed_type, self.module)))
                        ok = rel == orig_rel
                elif d.kind == K.RUNTIME_MISS:
                    ok = not mp and not tp
                elif d.kind == K.REVEAL_UNPAIRED:
                    ok = bool([x for x in m if x.revealed_type]) != bool([x for x in t if x.revealed_type])
                if ok and (need_runtime or d.kind == K.RUNTIME_MISS):
                    rt = self.runners.run_runtime(src)
                    ok = (rt.status == "exception" and classify_exception(rt.exc_type, rt.exc_message) == "strong"
                          and s.anchor in {vm.anchor(ln) for ln, _ in rt.frames})
                if ok:
                    return True
            return False

        return pred

    # ------------------------------------------------------------------ ddmin over statement lists
    def reduce(self, source: str, pred: Callable[[str], bool], protect_key: str | None = None) -> str:
        if "type: ignore" in source or "ty: ignore" in source:
            return source  # ast.unparse would drop the comments the case depends on
        self.tests = 0
        current = ast.unparse(ast.parse(source)) + "\n"
        if not self._test(pred, current):
            return source  # round-tripping alone changes behaviour (or the case is flaky): keep the original
        progress = True
        while progress and self.tests < self.max_tests:
            progress = False  # one full top-down pass over all statement lists; repeat while it shrinks
            tree = ast.parse(current)
            protected = _protected_ids(tree, protect_key)
            for owner, fname in _statement_lists(tree):
                if not _attached(tree, owner):
                    continue  # its subtree was deleted earlier in this pass
                items = list(getattr(owner, fname))
                n = 2
                while items and self.tests < self.max_tests:
                    chunk = max(1, len(items) // n)
                    removed = False
                    for start in range(0, len(items), chunk):
                        cut = items[start:start + chunk]
                        if any(id(x) in protected for x in cut):
                            continue
                        rest = items[:start] + items[start + chunk:]
                        setattr(owner, fname, rest or ([ast.Pass()] if fname in _NEEDS_BODY else []))
                        cand = ast.unparse(tree) + "\n"
                        if cand != current and self._test(pred, cand):
                            items, current, removed, progress = rest, cand, True, True
                            break
                        setattr(owner, fname, items)
                    if removed:
                        n = max(2, n - 1)  # ddmin: keep granularity after a successful removal
                        continue
                    if chunk == 1:
                        break
                    n = min(len(items), n * 2)
                setattr(owner, fname, items or ([ast.Pass()] if fname in _NEEDS_BODY else []))
        return current

    def _test(self, pred: Callable[[str], bool], src: str) -> bool:
        memo = self.__dict__.setdefault("_memo", {})
        if src in memo:
            return memo[src]
        self.tests += 1
        try:
            memo[src] = bool(pred(src))
        except Exception:  # noqa: BLE001 - a failing candidate is simply "not interesting"
            memo[src] = False
        return memo[src]


def _attached(tree: ast.Module, node: ast.AST) -> bool:
    return node is tree or any(n is node for n in ast.walk(tree))


def _safe_key(node: ast.AST) -> str:
    try:
        return statement_key(node)
    except Exception:  # noqa: BLE001
        return ""


def _statement_lists(tree: ast.Module) -> list[tuple[ast.AST, str]]:
    out: list[tuple[ast.AST, str]] = []
    queue: list[ast.AST] = [tree]
    while queue:
        node = queue.pop(0)
        for fname in ("body", "orelse", "finalbody"):
            sub = getattr(node, fname, None)
            if isinstance(sub, list) and sub and isinstance(sub[0], ast.stmt):
                out.append((node, fname))
                queue.extend(sub)
        for h in getattr(node, "handlers", []) or []:
            out.append((h, "body"))
            queue.extend(h.body)
        for c in getattr(node, "cases", []) or []:
            out.append((c, "body"))
            queue.extend(c.body)
    return out


def _protected_ids(tree: ast.Module, key: str | None) -> set[int]:
    """The statement under test and all of its ancestors must survive reduction."""
    if not key:
        return set()
    parents: dict[int, ast.AST] = {}
    target = None
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[id(child)] = node
        if target is None and isinstance(node, (ast.stmt, ast.match_case, ast.ExceptHandler)) and _safe_key(node) == key:
            target = node
    out: set[int] = set()
    while target is not None:
        out.add(id(target))
        target = parents.get(id(target))
    return out
