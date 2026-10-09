"""Which constructs could be responsible for a runtime failure at a statement?

CPython evidence says *that* a statement raised, not *why*. A repro that is reduced, or an issue that
quotes the crash, must not silently lose the construct that made it crash (the ty#4656 example crashed
only because of a ``list[Self]`` attribute, and its reduced repro had dropped that attribute).
This is a deterministic, syntactic dependency list; it names candidates, it does not prove a cause.
"""

from __future__ import annotations

import ast
import builtins

_SKIP = set(dir(builtins)) | {"reveal_type", "assert_type", "self", "cls"}


def _line(lines: list[str], n: int) -> str:
    return lines[n - 1].strip()[:70] if 0 < n <= len(lines) else ""


def dependency_constructs(tree: ast.AST | None, stmt: ast.AST | None, lines: list[str], limit: int = 8) -> list[str]:
    """Definitions in the program that the statement's names and attributes resolve to (by simple name)."""
    if tree is None or stmt is None:
        return []
    attrs = {n.attr for n in ast.walk(stmt) if isinstance(n, ast.Attribute)}
    names = {n.id for n in ast.walk(stmt) if isinstance(n, ast.Name)} - _SKIP
    found: list[str] = []

    def add(text: str) -> None:
        if text not in found:
            found.append(text)

    for n in ast.walk(tree):
        if n is stmt:
            continue
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in attrs:
            add(f"method `{n.name}` (L{n.lineno})")
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names:
            add(f"function `{n.name}` (L{n.lineno})")
        elif isinstance(n, ast.ClassDef) and n.name in names:
            add(f"class `{n.name}` (L{n.lineno})")
        elif isinstance(n, (ast.AnnAssign, ast.Assign)):
            targets = [n.target] if isinstance(n, ast.AnnAssign) else n.targets
            for t in targets:
                if isinstance(t, ast.Attribute) and t.attr in attrs:
                    ann = f": {ast.unparse(n.annotation)}" if isinstance(n, ast.AnnAssign) else ""
                    add(f"attribute `{t.attr}{ann}` (L{n.lineno}: `{_line(lines, n.lineno)}`)")
                elif isinstance(t, ast.Name) and (t.id in names or t.id in attrs):
                    add(f"binding of `{t.id}` (L{n.lineno}: `{_line(lines, n.lineno)}`)")
    return found[:limit]
