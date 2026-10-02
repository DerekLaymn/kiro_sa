"""Typing-feature tags for programs and statements (used for KB matching, dedup signatures,
strategy statistics and generator steering)."""

from __future__ import annotations

import ast

_NAME_TAGS = {
    "TypeVar": "typevar", "ParamSpec": "paramspec", "TypeVarTuple": "typevartuple", "Protocol": "protocol",
    "TypedDict": "typeddict", "overload": "overload", "dataclass": "dataclass", "dataclass_transform": "dataclass_transform",
    "Enum": "enum", "IntEnum": "enum", "StrEnum": "enum", "Flag": "enum", "Literal": "literal", "Final": "final",
    "final": "final", "ClassVar": "classvar", "Self": "self", "TypeIs": "typeis", "TypeGuard": "typeguard",
    "NamedTuple": "namedtuple", "NewType": "newtype", "Annotated": "annotated", "Unpack": "unpack",
    "Concatenate": "concatenate", "Callable": "callable", "Generic": "generic", "Any": "any", "cast": "cast",
    "assert_never": "assert_never", "Never": "never", "NoReturn": "never", "LiteralString": "literalstring",
    "Required": "typeddict", "NotRequired": "typeddict", "ReadOnly": "readonly", "override": "override",
    "abstractmethod": "abstract", "ABC": "abstract", "property": "property", "TypeAlias": "typealias",
    "Awaitable": "async", "Coroutine": "async", "Iterator": "iterator", "Generator": "generator",
    "isinstance": "isinstance", "issubclass": "isinstance", "hasattr": "hasattr", "callable": "callable_narrow",
    "len": "len", "super": "super", "assert_type": "assert_type", "reveal_type": "reveal_type",
    "Optional": "optional", "Union": "union", "type": "type_of",
}


def tags_for_nodes(nodes: list[ast.AST]) -> set[str]:
    tags: set[str] = set()
    for root in nodes:
        for n in ast.walk(root):
            if isinstance(n, ast.Name) and n.id in _NAME_TAGS:
                tags.add(_NAME_TAGS[n.id])
            elif isinstance(n, ast.Attribute) and n.attr in _NAME_TAGS:
                tags.add(_NAME_TAGS[n.attr])
            elif isinstance(n, ast.Match):
                tags.add("match")
            elif isinstance(n, ast.Compare):
                for op in n.ops:
                    if isinstance(op, (ast.Eq, ast.NotEq)):
                        tags.add("eq_narrow")
                    elif isinstance(op, (ast.In, ast.NotIn)):
                        tags.add("in_narrow")
                    elif isinstance(op, (ast.Is, ast.IsNot)):
                        tags.add("is_narrow")
            elif isinstance(n, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                tags.add("comprehension")
            elif isinstance(n, ast.Lambda):
                tags.add("lambda")
            elif isinstance(n, ast.NamedExpr):
                tags.add("walrus")
            elif isinstance(n, (ast.Await, ast.AsyncFunctionDef, ast.AsyncFor, ast.AsyncWith)):
                tags.add("async")
            elif isinstance(n, (ast.Yield, ast.YieldFrom)):
                tags.add("generator")
            elif isinstance(n, ast.TypeAlias if hasattr(ast, "TypeAlias") else ()):
                tags.add("type_stmt")
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and getattr(n, "type_params", None):
                tags.add("pep695")
                if any(isinstance(p, ast.ParamSpec) for p in n.type_params):
                    tags.add("paramspec")
                if any(isinstance(p, ast.TypeVarTuple) for p in n.type_params):
                    tags.add("typevartuple")
            elif isinstance(n, ast.FunctionDef) and n.decorator_list:
                tags.add("decorator")
            elif isinstance(n, ast.ClassDef) and any(k.arg == "metaclass" for k in n.keywords):
                tags.add("metaclass")
            elif isinstance(n, ast.FunctionDef) and n.name in ("__get__", "__set__"):
                tags.add("descriptor")
            elif isinstance(n, ast.FunctionDef) and n.name in ("__new__", "__init_subclass__", "__class_getitem__"):
                tags.add("constructor_magic")
            elif isinstance(n, ast.Starred):
                tags.add("star_unpack")
    return tags


def program_tags(tree: ast.Module | None) -> set[str]:
    return tags_for_nodes([tree]) if tree else set()
