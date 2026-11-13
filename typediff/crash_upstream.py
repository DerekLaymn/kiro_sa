"""Already-reported upstream CRASHES / hangs (``kind: "crash"`` entries of ``data/known_upstream.json``).

Crash findings never reach the discrepancy matcher in ``kb.py`` (the run has no discrepancy for them), so they are
matched here, from ``Pipeline._judge``, and closed as DUPLICATE. An entry matches only when ALL of these hold:
  tool        the crashing tool equals the entry's ``tool``  (one entry per tool: ty#4900 never closes mypy#22360)
  signature   regex, ``re.fullmatch`` against ``Crash.signature``
  requires    a pure function of the parsed program (``_CRASH_REQUIRES``); MANDATORY, so no entry can match on tool +
              signature alone (several different ty bugs share ``ty:signal-SIGABRT:stack-overflow``)
Any error inside a ``requires`` function, or a program that does not parse, means "no match".
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Callable, Iterable, Iterator

PATH = Path(__file__).parent / "data" / "known_upstream.json"


# --------------------------------------------------------------------------- AST helpers


class _Resolve(ast.NodeTransformer):
    """Replace string annotations (also nested ones such as ``N["C"]``) by their parsed expression."""

    def visit_Constant(self, node: ast.Constant):  # noqa: N802
        if isinstance(node.value, str):
            try:
                return self.visit(ast.parse(node.value.strip(), mode="eval").body)
            except SyntaxError:
                return node
        return node


def _resolve(node: ast.AST) -> ast.AST:
    import copy

    return _Resolve().visit(copy.deepcopy(node))


def _head(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _head(node.value)
    return None


def _subs(node: ast.AST, head: str | None = None) -> Iterator[ast.Subscript]:
    for n in ast.walk(node):
        if isinstance(n, ast.Subscript) and (head is None or _head(n.value) == head):
            yield n


def _names(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def _classes(tree: ast.Module) -> list[ast.ClassDef]:
    return [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]


def _functions(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _methods(c: ast.ClassDef) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [n for n in c.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _params(fn) -> list[ast.arg]:
    a = fn.args
    return [*a.posonlyargs, *a.args, *a.kwonlyargs]


def _annotation_roots(fn) -> list[ast.AST]:
    a = fn.args
    roots = [x.annotation for x in [*_params(fn), a.vararg, a.kwarg] if x is not None and x.annotation is not None]
    if fn.returns is not None:
        roots.append(fn.returns)
    return roots


def _type_params(node: ast.AST, kind: type | None = None) -> list:
    return [t for t in getattr(node, "type_params", []) if kind is None or isinstance(t, kind)]


def _module_calls(tree: ast.Module, kind: str) -> dict[str, ast.Call]:
    """Module-level ``NAME = TypeVar(...)`` / ``ParamSpec(...)`` assignments (also ``typing.`` / ``typing_extensions.``)."""
    out = {}
    for st in tree.body:
        if (isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name)
                and isinstance(st.value, ast.Call) and _head(st.value.func) == kind):
            out[st.targets[0].id] = st.value
    return out


def _kw(call: ast.Call, name: str) -> ast.AST | None:
    return next((k.value for k in call.keywords if k.arg == name), None)


def _is_true(node: ast.AST | None) -> bool:
    return isinstance(node, ast.Constant) and node.value is True


def _slice_elts(sub: ast.Subscript) -> list[ast.AST]:
    return list(sub.slice.elts) if isinstance(sub.slice, ast.Tuple) else [sub.slice]


def _is_union(node: ast.AST) -> bool:
    return (isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr)) or (
        isinstance(node, ast.Subscript) and _head(node.value) == "Union")


def _skip(tree: ast.AST, skipped: ast.AST) -> Iterator[ast.AST]:
    """Walk ``tree`` without descending into ``skipped``."""
    stack = [tree]
    while stack:
        n = stack.pop()
        if n is skipped:
            continue
        yield n
        stack.extend(ast.iter_child_nodes(n))


def _use_annotations(tree: ast.AST, skipped: ast.AST | None = None) -> Iterator[ast.AST]:
    """Resolved annotations of annotated assignments and function signatures (optionally outside one class)."""
    for n in (_skip(tree, skipped) if skipped is not None else ast.walk(tree)):
        if isinstance(n, ast.AnnAssign):
            yield _resolve(n.annotation)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for r in _annotation_roots(n):
                yield _resolve(r)


# --------------------------------------------------------------------------- requires: ty


def protocol_selfref_pair(tree: ast.Module) -> bool:
    """ty#4882: protocol A whose method takes ``A[..]``; another protocol B whose method takes a union holding both
    ``A[..]`` and ``B[..]``."""
    protos = [c for c in _classes(tree) if any(_head(b) == "Protocol" for b in c.bases)]
    for a in protos:
        a_self = any(_head(s) == a.name for m in _methods(a) for p in _params(m) if p.annotation is not None
                     for s in _subs(_resolve(p.annotation)))
        if not a_self:
            continue
        for b in protos:
            if b is a:
                continue
            for m in _methods(b):
                for p in _params(m):
                    if p.annotation is None:
                        continue
                    ann = _resolve(p.annotation)
                    heads = {_head(s) for s in _subs(ann)}
                    if _is_union(ann) and a.name in heads and b.name in heads:
                        return True
    return False


def nested_tuple_alias_compare(tree: ast.Module) -> bool:
    """ty#4883: a chain of >= 12 PEP 695 aliases ``type Tn = tuple[Tm, Tm]`` and a function comparing two parameters
    annotated with the top alias."""
    alias = {n.name.id: n.value for n in ast.walk(tree) if isinstance(n, ast.TypeAlias)}
    memo: dict[str, int] = {}

    def depth(name: str, seen: frozenset = frozenset()) -> int:
        if name in memo:
            return memo[name]
        v = alias.get(name)
        if name in seen or not isinstance(v, ast.Subscript) or _head(v.value) != "tuple":
            return 0
        kids = [e.id for e in _slice_elts(v) if isinstance(e, ast.Name) and e.id in alias]
        memo[name] = 1 + max((depth(k, seen | {name}) for k in kids), default=0)
        return memo[name]

    for fn in _functions(tree):
        ps = [p for p in _params(fn) if isinstance(p.annotation, ast.Name) and depth(p.annotation.id) >= 12]
        for x in ps:
            for y in ps:
                if x is not y and x.annotation.id == y.annotation.id and any(
                        isinstance(c, ast.Compare) and isinstance(c.left, ast.Name) and c.left.id == x.arg
                        and any(isinstance(o, ast.Name) and o.id == y.arg for o in c.comparators)
                        for c in ast.walk(fn)):
                    return True
    return False


def _callable_over(ann: ast.AST | None, ps: set[str], ret: set[str] | None) -> bool:
    """``Callable[P, R]`` with P in ``ps`` and (if ``ret`` is given) R a bare name in ``ret``."""
    if ann is None:
        return False
    a = _resolve(ann)
    if not isinstance(a, ast.Subscript) or _head(a.value) != "Callable":
        return False
    elts = _slice_elts(a)
    if len(elts) != 2 or not (isinstance(elts[0], ast.Name) and elts[0].id in ps):
        return False
    return ret is None or (isinstance(elts[1], ast.Name) and elts[1].id in ret)


def paramspec_self_application(tree: ast.Module) -> bool:
    """ty#4898: ``def F[**P, R](c: Callable[P, R])`` (or the old-style spelling) applied to itself: ``F(F)``."""
    mod_ps = set(_module_calls(tree, "ParamSpec"))
    mod_tv = set(_module_calls(tree, "TypeVar"))
    for fn in _functions(tree):
        ps = mod_ps | {t.name for t in _type_params(fn, ast.ParamSpec)}
        tv = mod_tv | {t.name for t in _type_params(fn, ast.TypeVar)}
        if not ps or not tv:
            continue
        if not any(_callable_over(p.annotation, ps, tv) for p in _params(fn)):
            continue
        if any(isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == fn.name
               and any(isinstance(a, ast.Name) and a.id == fn.name for a in c.args) for c in ast.walk(tree)):
            return True
    return False


def paramspec_self_callable_init(tree: ast.Module) -> bool:
    """ty#4899: class U whose ``__init__`` types ``self`` as ``Callable[P, T]`` and whose ``__call__`` (method or
    classmethod) does the same and takes one more named positional parameter before ``*args: P.args``; ``U()`` is called."""
    ps = set(_module_calls(tree, "ParamSpec"))
    for c in _classes(tree):
        ms = {m.name: m for m in _methods(c)}
        init, call = ms.get("__init__"), ms.get("__call__")
        if init is None or call is None:
            continue
        pi, pc = [*init.args.posonlyargs, *init.args.args], [*call.args.posonlyargs, *call.args.args]
        if not pi or len(pc) < 2 or call.args.vararg is None:
            continue
        if not (_callable_over(pi[0].annotation, ps, set(_module_calls(tree, "TypeVar")))
                and _callable_over(pc[0].annotation, ps, set(_module_calls(tree, "TypeVar")))):
            continue
        if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == c.name for n in ast.walk(tree)):
            return True
    return False


def expanding_generic_base(tree: ast.Module) -> bool:
    """ty#4900: generic class C with base ``N[N["C[C[X]]"]]`` (C inside its own argument), where N really uses its
    parameter (PEP 695 N must mention it in its body; old-style N must not be covariant), and an annotation outside
    C that is ``N[C[..]]``."""
    mod_tv = _module_calls(tree, "TypeVar")
    classes = {c.name: c for c in _classes(tree)}
    for c in classes.values():
        generic = bool(_type_params(c)) or any(_head(b) == "Generic" for b in c.bases)
        if not generic:
            continue
        for b in c.bases:
            rb = _resolve(b)
            n_name = _head(rb.value) if isinstance(rb, ast.Subscript) else None
            n = classes.get(n_name or "")
            if n is None or n is c or n_name in ("Generic", "Protocol"):
                continue
            expanding = any(_head(cs.value) == c.name and any(True for _ in _subs(cs.slice, c.name))
                            for inner in _subs(rb.slice, n_name) for cs in _subs(inner.slice, c.name))
            if not expanding:
                continue
            tps = _type_params(n)
            if tps:
                if not any(t.name in _names(ast.Module(body=n.body, type_ignores=[])) for t in tps):
                    continue
            else:
                gen = [bb for bb in n.bases if _head(bb) == "Generic" and isinstance(bb, ast.Subscript)]
                zs = [e.id for g in gen for e in _slice_elts(g) if isinstance(e, ast.Name)]
                if not zs or any(z in mod_tv and _is_true(_kw(mod_tv[z], "covariant")) for z in zs):
                    continue
            for ann in _use_annotations(tree, skipped=c):
                if any(any(True for _ in _subs(s.slice, c.name)) for s in _subs(ann, n_name)):
                    return True
    return False


# --------------------------------------------------------------------------- requires: mypy


def alias_via_generic_alias(tree: ast.Module) -> bool:
    """mypy#22343: ``type X = M[...X...]`` where ``M`` is another generic PEP 695 alias of this file whose right-hand
    side is itself a subscript (``type M[T] = type[T]``). A bare ``type Id[T] = T`` is a different (hanging) case."""
    aliases = {n.name.id: n for n in ast.walk(tree) if isinstance(n, ast.TypeAlias)}
    generic = {k for k, v in aliases.items() if v.type_params and isinstance(v.value, ast.Subscript)}
    for name, a in aliases.items():
        for s in _subs(a.value):
            h = _head(s.value)
            if h in generic and h != name and name in _names(s.slice):
                return True
    return False


def typevar_default_self(tree: ast.Module) -> bool:
    """mypy#22344: ``T = TypeVar("T", default="T")`` and a class ``Generic[T]``."""
    selfdef = set()
    for name, call in _module_calls(tree, "TypeVar").items():
        d = _kw(call, "default")
        if isinstance(d, ast.Constant) and d.value == name:
            selfdef.add(name)
    return bool(selfdef) and any(
        _head(b) == "Generic" and isinstance(b, ast.Subscript) and selfdef & _names(b.slice)
        for c in _classes(tree) for b in c.bases)


def contravariant_selfref_base(tree: ast.Module) -> bool:
    """mypy#22360: ``Z = TypeVar(.., contravariant=True)``, ``class N(Generic[Z])``, ``class C(N[N["..C.."]])`` and an
    annotation outside C that uses ``N[..]``."""
    contra = {k for k, v in _module_calls(tree, "TypeVar").items() if _is_true(_kw(v, "contravariant"))}
    classes = {c.name: c for c in _classes(tree)}
    ns = {c.name for c in classes.values()
          if any(_head(b) == "Generic" and isinstance(b, ast.Subscript) and contra & _names(b.slice) for b in c.bases)}
    for c in classes.values():
        for b in c.bases:
            rb = _resolve(b)
            n_name = _head(rb.value) if isinstance(rb, ast.Subscript) else None
            if n_name not in ns or n_name == c.name:
                continue
            if not any(c.name in _names(inner.slice) for inner in _subs(rb.slice, n_name)):
                continue
            if any(any(True for _ in _subs(ann, n_name)) for ann in _use_annotations(tree, skipped=c)):
                return True
    return False


def _type_leaves(n: ast.AST) -> Iterator[ast.AST]:
    """Members of a (resolved) annotation: ``A | B``, ``Union[A, B]``, ``Optional[A]`` and ``ClassVar[A]`` / ``Final[A]``
    are looked through; anything else (``tuple[..]``, ``Callable[..]``) is one opaque leaf."""
    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.BitOr):
        yield from _type_leaves(n.left)
        yield from _type_leaves(n.right)
    elif isinstance(n, ast.Subscript) and _head(n.value) in ("Union", "Optional", "ClassVar", "Final"):
        for e in _slice_elts(n):
            yield from _type_leaves(e)
    else:
        yield n


def call_attr_own_type(tree: ast.Module) -> bool:
    """ty#4148 / mypy#22361: a class whose ``__call__`` is declared as an ATTRIBUTE whose type leads back to the class
    (``__call__: C``, ``Self``, a union / ``Optional`` / ``ClassVar`` of those, or a cycle through other classes:
    ``A.__call__: B`` and ``B.__call__: A``, a chain of three), and an instance of that class, or of a subclass, being
    called (``C()()``, a name annotated with the class or with a union containing it, e.g. ``obj: C | Other``, or a name
    assigned from ``C()``: ``c = C(); c()``).
    Day-4 verification (results/days/day4-report.md): mutual pair, three-class chain, ``ClassVar``, ``"B | None"`` pairs and subclass
    instances all crash ty and mypy; ``__call__: int``, an unrelated class or ``list[C]`` do not (no cycle)."""
    classes = {c.name: c for c in _classes(tree)}
    edges: dict[str, set[str]] = {}
    for c in classes.values():
        for st in c.body:
            if isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name) and st.target.id == "__call__":
                for x in _type_leaves(_resolve(st.annotation)):
                    if isinstance(x, ast.Name) and (x.id == "Self" or x.id in classes):
                        edges.setdefault(c.name, set()).add(c.name if x.id == "Self" else x.id)

    def reaches_self(start: str) -> bool:
        seen, todo = set(), list(edges.get(start, ()))
        while todo:
            n = todo.pop()
            if n == start:
                return True
            if n not in seen:
                seen.add(n)
                todo.extend(edges.get(n, ()))
        return False

    family = {n for n in edges if reaches_self(n)}  # classes whose __call__ attribute leads back to themselves
    if not family:
        return False
    grew = True
    while grew:  # a subclass inherits the attribute
        grew = False
        for c in classes.values():
            if c.name not in family and any(_head(b) in family for b in c.bases):
                family.add(c.name)
                grew = True

    def in_family(ann: ast.AST | None) -> bool:
        return ann is not None and any(isinstance(x, ast.Name) and x.id in family for x in _type_leaves(_resolve(ann)))

    typed = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and in_family(n.annotation):
            typed.add(n.target.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            typed |= {p.arg for p in _params(n) if in_family(p.annotation)}
        elif (isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name)
              and n.value.func.id in family):  # ``c = C()`` then ``c()``: a local bound to an instance
            typed |= {t.id for t in n.targets if isinstance(t, ast.Name)}
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Call) and isinstance(f.func, ast.Name) and f.func.id in family:
                return True
            if isinstance(f, ast.Name) and f.id in typed:
                return True
    return False


def _is_name(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


# --------------------------------------------------------------------------- requires: pyright


def ctor_annotated_own_class(tree: ast.Module) -> bool:
    """pyright#11961: ``__init__`` / ``__new__`` declared as ``type["C"]`` in C itself (or a metaclass ``__call__``
    declared as ``type["C"]`` for ``class C(metaclass=Meta)``), and ``C()`` is called."""
    def own(ann: ast.AST, target: str) -> bool:
        a = _resolve(ann)
        return isinstance(a, ast.Subscript) and _head(a.value) == "type" and _is_name(a.slice, target)

    classes = _classes(tree)
    for c in classes:
        hit = any(isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name)
                  and st.target.id in ("__init__", "__new__") and own(st.annotation, c.name) for st in c.body)
        if not hit:
            for m in classes:
                meta = [k.value.id for k in c.keywords if k.arg == "metaclass" and isinstance(k.value, ast.Name)]
                if m.name in meta and any(isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name)
                                          and st.target.id == "__call__" and own(st.annotation, c.name) for st in m.body):
                    hit = True
        if hit and any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == c.name
                       for n in ast.walk(tree)):
            return True
    return False


def growing_recursive_alias(tree: ast.Module) -> bool:
    """pyright#11960: ``type A[T] = ...A[... A ...]...`` (the argument of the recursive use itself mentions A) and a
    specialisation ``A[..]`` in an annotation."""
    for a in (n for n in ast.walk(tree) if isinstance(n, ast.TypeAlias)):
        name = a.name.id
        if not a.type_params:
            continue
        if not any(name in _names(s.slice) for s in _subs(a.value, name)):
            continue
        if any(any(True for _ in _subs(ann, name)) for ann in _use_annotations(tree, skipped=a)):
            return True
    return False


_CRASH_REQUIRES: dict[str, Callable[[ast.Module], bool]] = {
    "protocol_selfref_pair": protocol_selfref_pair,
    "nested_tuple_alias_compare": nested_tuple_alias_compare,
    "paramspec_self_application": paramspec_self_application,
    "paramspec_self_callable_init": paramspec_self_callable_init,
    "expanding_generic_base": expanding_generic_base,
    "alias_via_generic_alias": alias_via_generic_alias,
    "typevar_default_self": typevar_default_self,
    "contravariant_selfref_base": contravariant_selfref_base,
    "call_attr_own_type": call_attr_own_type,
    "ctor_annotated_own_class": ctor_annotated_own_class,
    "growing_recursive_alias": growing_recursive_alias,
}


# --------------------------------------------------------------------------- loader / matcher


def load(path: Path = PATH) -> list[dict]:
    if not path.exists():
        return []
    return [e for e in json.loads(path.read_text(encoding="utf-8")).get("entries", []) if e.get("kind") == "crash"]


def match_crash(source: str, tool: str, signature: str, path: Path = PATH) -> dict | None:
    """The first crash entry for ``tool`` whose signature regex matches and whose ``requires`` holds on ``source``."""
    entries = load(path)
    if not entries:
        return None
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None
    for e in entries:
        if e.get("tool") != tool:
            continue
        req = _CRASH_REQUIRES.get(e.get("requires", ""))
        if req is None or not re.fullmatch(e.get("signature", "(?!)"), signature or ""):
            continue
        try:
            if req(tree):
                return e
        except Exception:  # noqa: BLE001 - a broken matcher must never break the pipeline
            continue
    return None


__all__ = ["load", "match_crash", "_CRASH_REQUIRES"]
