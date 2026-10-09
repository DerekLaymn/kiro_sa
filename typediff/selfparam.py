"""AST helpers for one narrow pattern: a method with ``Self`` in a NON-receiver parameter, called through a
subclass instance (ty#4656). Shared by the KB matcher, the spec-desugar experiment and the LSP probe.

The pattern is deliberately a *hint source*, not a rule: ty solves ``Self`` jointly with the receiver (the
spec's own TypeVar desugaring), mypy/pyright pin it to the receiver. Nothing here decides who is right.
stdlib only.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass

from .models import Diagnostic

_MYPY_ARG = re.compile(r'Argument (?:\d+|"\w+") to "(?P<m>\w+)" of "(?P<c>[\w.]+)" has incompatible type '
                       r'"(?P<found>.+)"; expected "(?P<expected>.+)"$')
_NAME = re.compile(r"[A-Za-z_]\w*")
_MODULE_PREFIX = re.compile(r"\b[a-z_]\w*\.(?=[A-Za-z_])")


def classes_by_name(tree: ast.AST) -> dict[str, ast.ClassDef]:
    out: dict[str, ast.ClassDef] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef):
            out.setdefault(n.name, n)
    return out


def _base_name(b: ast.expr) -> str:
    if isinstance(b, ast.Subscript):
        b = b.value
    return b.id if isinstance(b, ast.Name) else b.attr if isinstance(b, ast.Attribute) else ""


def mro(name: str, classes: dict[str, ast.ClassDef]) -> list[str]:
    """Approximate MRO by simple class name (depth first, left to right). Unknown bases are skipped."""
    out: list[str] = []

    def visit(n: str) -> None:
        if n in out or n not in classes:
            return
        out.append(n)
        for b in classes[n].bases:
            visit(_base_name(b))

    visit(name)
    return out


def method_def(cls: ast.ClassDef, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    for n in cls.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None


def decorator_names(fn: ast.AST) -> set[str]:
    return {d.id if isinstance(d, ast.Name) else getattr(d, "attr", "") for d in getattr(fn, "decorator_list", [])}


def mentions_self(ann: ast.AST | None) -> bool:
    return ann is not None and any((isinstance(x, ast.Name) and x.id == "Self") or (isinstance(x, ast.Attribute) and x.attr == "Self")
                                   for x in ast.walk(ann))


def nonreceiver_params(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.arg]:
    pos = [*fn.args.posonlyargs, *fn.args.args]
    if "staticmethod" not in decorator_names(fn):
        pos = pos[1:]
    return [*pos, *fn.args.kwonlyargs, *[a for a in (fn.args.vararg, fn.args.kwarg) if a is not None]]


def self_in_nonreceiver_params(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(mentions_self(p.annotation) for p in nonreceiver_params(fn))


def first_definer(cls_name: str, method: str, classes: dict[str, ast.ClassDef]) -> str | None:
    """The first class (in approximate MRO order, starting with ``cls_name`` itself) that defines ``method``."""
    for c in mro(cls_name, classes):
        if method_def(classes[c], method) is not None:
            return c
    return None


@dataclass
class SelfParamCall:
    method: str
    defining: str  # class that defines the method (and owns the Self parameter)
    receiver: str  # strict subclass the call goes through (what mypy/pyright pin Self to)
    argument: str  # the rejected argument's class (the defining class or a supertype of the receiver)
    call: ast.Call


def _bare(t: str) -> str:
    m = _NAME.search(t)
    return m.group(0) if m else ""


def match_self_param_call(tree: ast.AST | None, mypy_diags: list[Diagnostic], stmt: ast.AST | None) -> SelfParamCall | None:
    """ALL of: a class method has Self inside a non-receiver parameter annotation; the checker's rejection names a
    strict subclass of the defining class as the expected type with no override in between; the rejected argument is
    the defining class or a supertype of the receiver; and the statement contains a call to that method."""
    if tree is None or stmt is None:
        return None
    classes = classes_by_name(tree)
    for x in mypy_diags:
        if x.code != "arg-type":
            continue
        m = _MYPY_ARG.search(x.message)
        if not m:
            continue
        found, expected = (_MODULE_PREFIX.sub("", m["found"]), _MODULE_PREFIX.sub("", m["expected"]))
        ft, et = _NAME.findall(found), _NAME.findall(expected)
        if len(ft) == len(et) and _NAME.sub("N", found) == _NAME.sub("N", expected):
            pairs = [(a, b) for a, b in zip(ft, et) if a != b]
        else:  # e.g. Box[int] vs IntBox: compare the class names only
            pairs = [(_bare(found), _bare(expected))] if _bare(found) != _bare(expected) else []
        if not pairs:
            continue
        method, defining = m["m"], _MODULE_PREFIX.sub("", m["c"])
        ok = defining in classes
        fn = method_def(classes[defining], method) if ok else None
        ok = ok and fn is not None and self_in_nonreceiver_params(fn)
        for arg_cls, recv in pairs:
            if not ok:
                break
            ok = (recv in classes and recv != defining and defining in mro(recv, classes)
                  and first_definer(recv, method, classes) == defining  # not overridden between receiver and definer
                  and (arg_cls == "object" or arg_cls in mro(recv, classes)))  # argument is a supertype of the receiver
        if not ok:
            continue
        call = next((c for c in ast.walk(stmt) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                     and c.func.attr == method), None)
        if call is not None:
            return SelfParamCall(method, defining, pairs[0][1], pairs[0][0], call)
    return None


def has_self_typed_state(tree: ast.AST | None) -> bool:
    """A class declares an attribute whose annotation mentions Self (``children: list[Self]``, ``next: Self | None``).
    ty specialises such attributes to the receiver, so together with a jointly-solved Self parameter it is unsound."""
    if tree is None:
        return False
    for cls in (c for c in ast.walk(tree) if isinstance(c, ast.ClassDef)):
        for n in cls.body:  # class-level declaration: `next: Self | None`
            if isinstance(n, ast.AnnAssign) and mentions_self(n.annotation):
                return True
        for n in ast.walk(cls):  # instance attribute declared in a method: `self.children: list[Self] = []`
            if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Attribute) and mentions_self(n.annotation):
                return True
    return False


def simple_instance_expr(node: ast.AST, classes: dict[str, ast.ClassDef]) -> bool:
    """``Cls()`` for a class defined in the program whose construction needs no arguments."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.args and not node.keywords):
        return False
    cls = node.func.id
    if cls not in classes:
        return False
    init = next((method_def(classes[c], "__init__") for c in mro(cls, classes) if method_def(classes[c], "__init__")), None)
    if init is None:
        return True
    a = init.args
    required_positional = len(a.posonlyargs) + len(a.args) - len(a.defaults) - 1  # minus the receiver
    return required_positional <= 0 and all(d is not None for d in a.kw_defaults)
