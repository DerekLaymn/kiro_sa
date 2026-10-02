"""Map physical lines to *statement anchors*.

Checkers legitimately report the same problem at different lines/columns of one statement
(mypy at the call, ty at the argument on the next line; decorators vs ``def``). Comparing
per-statement instead of per-line removes that whole class of cosmetic noise.

Every statement also gets a stable *path* (``f.body[2]``) used to compare a program with its
metamorphic variants, whose line numbers differ after ``ast.unparse``.
"""

from __future__ import annotations

import ast
import copy
from dataclasses import dataclass, field

_HEADER_PREFIXES = ("elif", "else", "except", "finally", "case")


@dataclass
class Statement:
    anchor: int  # first line (incl. decorators)
    end: int  # last line of the header (compound) or of the statement (simple)
    node_type: str
    scope: str
    path: str
    text: str
    node: ast.AST = field(repr=False, default=None)
    insertable: bool = True  # can we put a new statement right before it?


class AnchorMap:
    def __init__(self, source: str):
        self.source = source
        self.lines = source.splitlines()
        self.line_to_stmt: dict[int, Statement] = {}
        self.statements: list[Statement] = []
        self.by_path: dict[str, Statement] = {}
        self.tree: ast.Module | None = None
        self.syntax_error: str | None = None
        try:
            self.tree = ast.parse(source)
        except SyntaxError as exc:  # invalid test program; caller decides
            self.syntax_error = f"{exc.msg} (line {exc.lineno})"
            return
        self._visit_body(self.tree.body, scope="<module>", path="")

    # ------------------------------------------------------------------ build
    def _visit_body(self, body: list[ast.stmt], scope: str, path: str, field_name: str = "body") -> None:
        for i, node in enumerate(body):
            p = f"{path}{field_name}[{i}]" if not path else f"{path}.{field_name}[{i}]"
            self._visit_stmt(node, scope, p)

    def _visit_stmt(self, node: ast.stmt, scope: str, path: str) -> None:
        start = node.lineno
        decos = getattr(node, "decorator_list", None) or []
        if decos:
            start = min(start, *(d.lineno for d in decos))
        body = getattr(node, "body", None)
        if isinstance(body, list) and body and isinstance(body[0], ast.AST):
            first = body[0].lineno
            header_end = max(node.lineno, first - 1) if first > node.lineno else node.lineno
        else:
            header_end = node.end_lineno or node.lineno
        text = self.lines[node.lineno - 1].strip() if node.lineno - 1 < len(self.lines) else ""
        st = Statement(
            anchor=start, end=header_end, node_type=type(node).__name__, scope=scope, path=path, text=text, node=node,
            insertable=not text.startswith(_HEADER_PREFIXES),
        )
        self.statements.append(st)
        self.by_path[path] = st
        for ln in range(start, header_end + 1):
            self.line_to_stmt[ln] = st

        inner_scope = scope
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            inner_scope = node.name if scope == "<module>" else f"{scope}.{node.name}"
        for fname in ("body", "orelse", "finalbody"):
            sub = getattr(node, fname, None)
            if isinstance(sub, list) and sub and isinstance(sub[0], ast.stmt):
                self._visit_body(sub, inner_scope, path, fname)
        for hi, handler in enumerate(getattr(node, "handlers", []) or []):
            hp = f"{path}.handlers[{hi}]"
            first = handler.body[0].lineno if handler.body else handler.lineno
            hst = Statement(handler.lineno, max(handler.lineno, first - 1), "ExceptHandler", inner_scope, hp,
                            self.lines[handler.lineno - 1].strip(), handler, insertable=False)
            self.statements.append(hst)
            self.by_path[hp] = hst
            for ln in range(hst.anchor, hst.end + 1):
                self.line_to_stmt[ln] = hst
            self._visit_body(handler.body, inner_scope, hp, "body")
        for ci, case in enumerate(getattr(node, "cases", []) or []):
            cp = f"{path}.cases[{ci}]"
            cl = case.pattern.lineno
            first = case.body[0].lineno if case.body else cl
            cst = Statement(cl, max(cl, first - 1), "match_case", inner_scope, cp, self.lines[cl - 1].strip(), case,
                            insertable=False)
            self.statements.append(cst)
            self.by_path[cp] = cst
            for ln in range(cst.anchor, cst.end + 1):
                self.line_to_stmt[ln] = cst
            self._visit_body(case.body, inner_scope, cp, "body")

    # ------------------------------------------------------------------ queries
    def stmt(self, line: int) -> Statement | None:
        return self.line_to_stmt.get(line)

    def anchor(self, line: int) -> int:
        st = self.line_to_stmt.get(line)
        return st.anchor if st else line

    def span(self, anchor: int) -> tuple[int, int]:
        st = self.line_to_stmt.get(anchor)
        return (st.anchor, st.end) if st else (anchor, anchor)

    def scope(self, line: int) -> str:
        st = self.line_to_stmt.get(line)
        return st.scope if st else "<module>"

    def path(self, line: int) -> str | None:
        st = self.line_to_stmt.get(line)
        return st.path if st else None

    def enclosing_nodes(self, line: int) -> list[ast.AST]:
        """Outer-to-inner chain of AST nodes (statements, handlers, match cases) containing ``line``."""
        if not self.tree:
            return []
        chain: list[ast.AST] = []

        def bounds(n: ast.AST) -> tuple[int, int]:
            if isinstance(n, ast.match_case):
                lo = n.pattern.lineno
                hi = max([lo] + [getattr(s, "end_lineno", lo) or lo for s in n.body])
                return lo, hi
            lo = min([n.lineno] + [d.lineno for d in getattr(n, "decorator_list", []) or []])
            return lo, getattr(n, "end_lineno", n.lineno) or n.lineno

        def visit(nodes: list[ast.AST]) -> None:
            for n in nodes:
                lo, hi = bounds(n)
                if lo <= line <= hi:
                    chain.append(n)
                    for fname in ("body", "orelse", "finalbody", "handlers", "cases"):
                        sub = getattr(n, fname, None)
                        if isinstance(sub, list) and sub and isinstance(sub[0], ast.AST):
                            visit(sub)
                    return

        visit(self.tree.body)
        return chain


def statement_key(node: ast.AST) -> str:
    """Body-independent source key used to find 'the same statement' in a reduced program."""
    if isinstance(node, ast.match_case):
        return "case " + ast.unparse(node.pattern)
    if isinstance(node, ast.ExceptHandler):
        return "except " + (ast.unparse(node.type) if node.type else "") + (f" as {node.name}" if node.name else "")
    if isinstance(getattr(node, "body", None), list):
        clone = copy.deepcopy(node)
        for fname in ("body", "orelse", "finalbody", "handlers", "cases"):
            if isinstance(getattr(clone, fname, None), list):
                setattr(clone, fname, [ast.Pass()] if fname == "body" else [])
        try:
            return ast.unparse(clone).split("\n", 1)[0]
        except Exception:  # noqa: BLE001 - unparse of a gutted node may fail on exotic nodes
            return type(node).__name__
    return ast.unparse(node)
