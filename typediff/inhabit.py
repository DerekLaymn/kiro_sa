"""Runtime-inhabitation oracle: does a value observed by CPython belong to a revealed type?

Returns True / False / None (= cannot decide). Only definite ``False`` answers are used as
RUNTIME evidence ("checker X claims this expression has type T, but CPython produced a value
outside T"), so every rule here errs towards ``None``.
"""

from __future__ import annotations

from .typenorm import NormType, TNode

_BUILTIN_NOMINAL = {
    "int", "str", "bytes", "bytearray", "float", "complex", "bool", "list", "dict", "set", "frozenset",
    "tuple", "type", "range", "slice", "memoryview",
}
_ALWAYS = {"object", "Any", "Unknown", "Divergent", "..."}


def _short(qual: str) -> str:
    """'builtins.int' -> 'int', '__main__.A.B' -> 'A.B'."""
    for prefix in ("builtins.", "__main__.", "case."):
        if qual.startswith(prefix):
            return qual[len(prefix):]
    return qual.rsplit(".", 1)[-1] if qual.count(".") >= 1 and qual.split(".")[0] in ("collections", "enum", "abc", "typing") else qual


def _mro_names(shape: dict) -> set[str]:
    names = set()
    for q in shape.get("mro", []):
        s = _short(q)
        names.add(s)
        names.add(s.rsplit(".", 1)[-1])
    return names


def inhabits(shape: dict, t: NormType | None, nominal_user_classes: set[str] = frozenset()) -> bool | None:
    if t is None or t.node is None:
        return None
    return _check(shape, t.node, nominal_user_classes, exact_float="exact_float" in t.flags)


def _check(shape: dict, node: TNode, nominal: set[str], exact_float: bool = False) -> bool | None:
    if node.kind == "union":
        results = [_check(shape, m, nominal, exact_float) for m in node.args]
        if any(r is True for r in results):
            return True
        return False if all(r is False for r in results) else None
    if node.kind == "inter":
        results = [_check(shape, m, nominal, exact_float) for m in node.args]
        if any(r is False for r in results):
            return False
        return True if all(r is True for r in results) else None
    if node.kind == "neg":
        r = _check(shape, node.args[0], nominal, exact_float)
        return None if r is None else not r
    if node.kind == "literal":
        if shape.get("enum"):
            return shape["enum"].split(".")[-2:] == node.name.split(".")[-2:]
        lit = shape.get("literal")
        if lit is None or _short(shape.get("type", "")) not in ("int", "str", "bool", "bytes"):
            # Literal types are inhabited only by exact int/str/bool/bytes instances or enum members
            # (instances of str/int subclasses are excluded - see ty docs, strict-equality-semantics).
            return False
        return _lit_eq(lit, node.name)
    if node.kind != "name":
        return None

    name = node.name
    if name in _ALWAYS:
        return True
    if name in ("None",):
        return shape.get("type") == "builtins.NoneType"
    if name == "Never":
        return False
    mro = _mro_names(shape)
    if name == "float":
        if exact_float:
            return "float" in mro
        return bool(mro & {"float", "int"})  # typing spec numeric promotion
    if name == "complex":
        return bool(mro & {"complex", "float", "int"})
    if name == "type" and node.args:
        if not shape.get("is_class"):
            return False
        inner = node.args[0]
        if inner.kind == "name" and not inner.args:
            cls_names = {_short(q).rsplit(".", 1)[-1] for q in shape.get("class_mro", [])}
            if inner.name in _ALWAYS:
                return True
            if inner.name in _BUILTIN_NOMINAL or inner.name in nominal:
                return inner.name in cls_names
        return None
    if name in ("Callable",):
        return True if shape.get("callable") else False

    base = name.rsplit(".", 1)[-1]
    if base in _BUILTIN_NOMINAL or base in nominal:
        if base not in mro and name not in mro:
            return False
        return _check_args(shape, base, node.args, nominal)
    return None  # protocols, TypedDicts, NewTypes, TypeVars, ABCs ... -> undecidable here


def _check_args(shape: dict, base: str, args: list[TNode], nominal: set[str]) -> bool | None:
    if not args:
        return True
    if base in ("list", "set", "frozenset") and len(args) == 1:
        return _all(shape.get("items"), args[0], nominal, complete=shape.get("len", 0) <= len(shape.get("items", [])))
    if base == "tuple":
        items = shape.get("items")
        if items is None:
            return None
        if len(args) == 2 and args[1].kind == "name" and args[1].name == "...":
            return _all(items, args[0], nominal, complete=shape.get("len", 0) <= len(items))
        if shape.get("len") is not None and shape["len"] != len(args):
            return False
        results = [_check(s, a, nominal) for s, a in zip(items, args)]
        if any(r is False for r in results):
            return False
        return True if all(r is True for r in results) and len(items) == len(args) else None
    if base == "dict" and len(args) == 2:
        pairs = shape.get("dict_items")
        if pairs is None:
            return None
        res = []
        for k, v in pairs:
            res += [_check(k, args[0], nominal), _check(v, args[1], nominal)]
        if any(r is False for r in res):
            return False
        return True if all(r is True for r in res) and shape.get("len", 0) <= len(pairs) else None
    return None


def _all(items, arg: TNode, nominal: set[str], complete: bool) -> bool | None:
    if items is None:
        return None
    res = [_check(s, arg, nominal) for s in items]
    if any(r is False for r in res):
        return False
    return True if all(r is True for r in res) and complete else None


def _lit_eq(runtime_repr: str, literal: str) -> bool | None:
    try:
        import ast

        return ast.literal_eval(runtime_repr) == ast.literal_eval(literal) and type(ast.literal_eval(runtime_repr)) is type(
            ast.literal_eval(literal)
        )
    except (ValueError, SyntaxError):
        return None
