"""LLM program generation + deterministic preflight lint (rejects INVALID_TEST programs before
they cost three checker runs and an adjudication)."""

from __future__ import annotations

import ast
import sys

from . import prompts
from .llm import complete_json

_STDLIB = set(getattr(sys, "stdlib_module_names", ())) | {"typing_extensions", "__future__"}
_EMPTY_OK_DECOS = {"overload", "abstractmethod", "abstractproperty"}


def preflight(source: str, target_python: str = "3.12") -> list[str]:
    """Return blocking problems ('ERROR: ...') and warnings ('WARN: ...')."""
    out: list[str] = []
    try:
        major, minor = (int(x) for x in target_python.split("."))
        tree = ast.parse(source, feature_version=(major, minor))
    except SyntaxError as exc:
        return [f"ERROR: syntax error for Python {target_python}: {exc.msg} (line {exc.lineno})"]
    protocols = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef) and any(getattr(b, "id", getattr(b, "attr", "")) == "Protocol" or
                                               (isinstance(b, ast.Subscript) and getattr(b.value, "id", "") == "Protocol")
                                               for b in n.bases):
            protocols.add(n.name)
    called = {getattr(c.func, "id", getattr(c.func, "attr", None)) for c in ast.walk(tree) if isinstance(c, ast.Call)}
    referenced = {x.id for x in ast.walk(tree) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load)}
    for n in ast.walk(tree):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            mods = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module or ""]
            for m in mods:
                if m and m.split(".")[0] not in _STDLIB and not (getattr(n, "level", 0) or 0):
                    out.append(f"ERROR: non-stdlib import {m!r} (environment-dependent -> CONFIG_ARTIFACT noise)")
        if isinstance(n, ast.ClassDef):
            for item in n.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    _check_empty(item, n.name in protocols, out)
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _check_empty(n, False, out)
            if n.name not in called and n.name not in referenced:
                out.append(f"WARN: function {n.name!r} is never called - CPython cannot act as an oracle for it")
        if isinstance(n, ast.ClassDef) and n.name not in referenced and n.name not in called:
            out.append(f"WARN: class {n.name!r} is never used at runtime")
    text = source
    for bad in ("import random", "from random", "time.time(", "input(", "open(", "os.environ", "sys.argv", "threading"):
        if bad in text:
            out.append(f"ERROR: nondeterministic or I/O construct {bad!r}")
    return out


def _check_empty(fn: ast.AST, in_protocol: bool, out: list[str]) -> None:
    decos = {getattr(d, "id", getattr(d, "attr", "")) for d in fn.decorator_list}
    body = [s for s in fn.body if not (isinstance(s, ast.Expr) and isinstance(getattr(s, "value", None), ast.Constant)
                                        and isinstance(s.value.value, str))]
    trivial = all(isinstance(s, ast.Pass) or (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and s.value.value is ...)
                  for s in body)
    returns_value = fn.returns is not None and not (isinstance(fn.returns, ast.Constant) and fn.returns.value is None)
    if trivial and returns_value and not in_protocol and not (decos & _EMPTY_OK_DECOS):
        out.append(f"WARN: {fn.name!r} has an empty body but a non-None return type (both checkers report empty-body)")


def blocking(problems: list[str]) -> bool:
    return any(p.startswith("ERROR") for p in problems)


def generate(llm, area: str, brief: str, mutations: list, previous: str, avoid: list[str], target_python: str = "3.12",
             retries: int = 1) -> tuple[str | None, dict]:
    system = prompts.GENERATOR_SYSTEM.format(target_python=target_python, avoid="; ".join(avoid) or "(none)")
    user = prompts.GENERATOR_USER.format(area=area, brief=brief, mutations=mutations or "(none)", previous=previous or "")
    meta: dict = {}
    for _ in range(retries + 1):
        obj = complete_json(llm, system, user, lambda o: [] if isinstance(o, dict) and isinstance(o.get("source"), str) else ["need 'source'"],
                            temperature=0.8, max_tokens=3000)
        if obj.get("_null") or obj.get("_invalid"):
            return None, {"error": "generator unavailable"}
        src = obj["source"]
        problems = preflight(src, target_python)
        meta = {"hypothesis": obj.get("hypothesis", ""), "features": obj.get("features", []), "preflight": problems}
        if not blocking(problems):
            return src, meta
        user += "\n\nYour previous program was rejected by the preflight lint:\n" + "\n".join(problems) + "\nFix it."
    return None, meta
