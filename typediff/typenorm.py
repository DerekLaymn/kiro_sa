"""Normalise revealed-type strings from mypy / ty / pyright into one canonical spelling,
and classify how two revealed types relate.

The goal is NOT a full type parser; it is to make sure that purely cosmetic differences
(``builtins.int`` vs ``int``, ``Optional[X]`` vs ``X | None``, ``Literal['a']`` vs
``Literal["a"]``, union member order, ``float*``) never reach the LLM as "discrepancies",
while anything we cannot parse is reported as UNCOMPARABLE (never silently EQUAL).
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass, field

GRADUAL_NAMES = {"Any", "Unknown", "Divergent"}
_STRIP_MODULES = (
    "builtins.", "typing_extensions.", "typing.", "collections.abc.", "_collections_abc.",
    "_typeshed.", "abc.", "types.", "enum.", "__main__.", "case.",
)
_ALIASES = {
    "List": "list", "Dict": "dict", "Set": "set", "FrozenSet": "frozenset", "Tuple": "tuple",
    "Type": "type", "NoneType": "None", "NoReturn": "Never", "<nothing>": "Never",
    "DefaultDict": "defaultdict", "Deque": "deque",
}
_LITERAL_BASES = {"int", "str", "bool", "bytes"}
# concrete runtime classes ty reveals vs the abstract types mypy reveals (types.CoroutineType <: Coroutine, ...)
_RUNTIME_SUBCLASS = {"CoroutineType": "Coroutine", "GeneratorType": "Generator",
                     "AsyncGeneratorType": "AsyncGenerator"}


class Relation(str, enum.Enum):
    EQUAL = "equal"
    COSMETIC = "cosmetic"  # equal modulo display conventions (float*, mypy's Literal[..]?)
    GRADUAL = "gradual"  # at least one side contains Any/Unknown/@Todo/Divergent
    TODO = "todo"  # ty reports @Todo -> known unimplemented feature
    PRECISION_A = "a_more_precise"  # A is a strict refinement of B (subset / literal of)
    PRECISION_B = "b_more_precise"
    DIFFERENT = "different"
    UNCOMPARABLE = "uncomparable"  # callables, overloads, unparsable text


# --------------------------------------------------------------------------- tiny type AST


@dataclass
class TNode:
    kind: str  # name | union | inter | neg | literal | opaque
    name: str = ""
    args: list["TNode"] = field(default_factory=list)
    flags: set[str] = field(default_factory=set)

    def render(self) -> str:
        if self.kind == "union":
            return " | ".join(a.render() for a in self.args)
        if self.kind == "inter":
            return " & ".join(a.render() for a in self.args)
        if self.kind == "neg":
            return "~" + self.args[0].render()
        if self.kind == "literal":
            return f"Literal[{self.name}]"
        if self.kind == "opaque":
            return self.name
        if self.args or "empty_args" in self.flags:
            return f"{self.name}[{', '.join(a.render() for a in self.args)}]"
        return self.name

    def walk(self):
        yield self
        for a in self.args:
            yield from a.walk()


_TOKEN = re.compile(
    r"""\s*(?:(?P<str>'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")|(?P<punct>[\[\](),|&~])|(?P<ellipsis>\.\.\.)|(?P<word>[^\s\[\](),|&~'"]+))"""
)


class _Parser:
    def __init__(self, text: str):
        self.toks: list[tuple[str, str]] = []
        pos = 0
        while pos < len(text):
            m = _TOKEN.match(text, pos)
            if not m or m.end() == pos:
                if text[pos:].strip() == "":
                    break
                raise ValueError(f"cannot tokenize at {text[pos:]!r}")
            pos = m.end()
            for k in ("str", "punct", "ellipsis", "word"):
                if m.group(k) is not None:
                    self.toks.append((k, m.group(k)))
                    break
        self.i = 0

    def peek(self) -> str | None:
        return self.toks[self.i][1] if self.i < len(self.toks) else None

    def take(self) -> tuple[str, str]:
        tok = self.toks[self.i]
        self.i += 1
        return tok

    def parse(self) -> TNode:
        node = self.union()
        if self.i != len(self.toks):
            raise ValueError("trailing tokens")
        return node

    def union(self) -> TNode:
        parts = [self.inter()]
        while self.peek() == "|":
            self.take()
            parts.append(self.inter())
        return parts[0] if len(parts) == 1 else TNode("union", args=parts)

    def inter(self) -> TNode:
        parts = [self.unary()]
        while self.peek() == "&":
            self.take()
            parts.append(self.unary())
        return parts[0] if len(parts) == 1 else TNode("inter", args=parts)

    def unary(self) -> TNode:
        if self.peek() == "~":
            self.take()
            return TNode("neg", args=[self.unary()])
        if self.peek() == "(":
            self.take()
            inner = self.union()
            if self.peek() != ")":
                raise ValueError("expected )")
            self.take()
            return inner
        return self.atom()

    def atom(self) -> TNode:
        kind, tok = self.take()
        if kind == "ellipsis":
            return TNode("name", name="...")
        if kind == "str":
            return TNode("name", name=tok)
        if kind != "word":
            raise ValueError(f"unexpected {tok!r}")
        if tok in ("def", "Overload") or tok.startswith("def"):
            raise ValueError("callable")
        node = TNode("name", name=tok)
        if self.peek() == "[":
            self.take()
            if self.peek() == "]":
                self.take()
                node.flags.add("empty_args")
                return node
            node.args.append(self.union())
            while self.peek() == ",":
                self.take()
                node.args.append(self.union())
            if self.peek() != "]":
                raise ValueError("expected ]")
            self.take()
        return node


# --------------------------------------------------------------------------- normalisation


@dataclass
class NormType:
    raw: str
    text: str  # canonical rendering
    node: TNode | None
    flags: set[str]  # mypy_inferred_literal, exact_float, gradual, todo, opaque

    @property
    def comparable(self) -> bool:
        return self.node is not None


def _pre(raw: str, module: str) -> tuple[str, set[str]]:
    flags: set[str] = set()
    t = raw.strip()
    if "@Todo" in t:
        flags.add("todo")
    t = re.sub(r"@Todo(\([^)]*\))?", "Unknown", t)
    if re.search(r"Literal\[[^\]]*\]\?", t):
        flags.add("mypy_inferred_literal")
        t = re.sub(r"(Literal\[[^\]]*\])\?", r"\1", t)
    if re.search(r"\b(float|complex)\*", t):
        flags.add("exact_float")
        t = re.sub(r"\b(float|complex)\*", r"\1", t)
    if re.search(r"\w\?", t):  # mypy marks inferred/unsolved types with '?', e.g. A[T?]
        flags.add("mypy_inferred")
        t = re.sub(r"(\w)\?", r"\1", t)
    # mypy ad-hoc intersections: <subclass of "A" and "B">
    t = re.sub(
        r'<subclass of ((?:"[^"]+"(?:,| and)?\s*)+)>',
        lambda m: " & ".join(re.findall(r'"([^"]+)"', m.group(1))),
        t,
    )
    t = re.sub(r"<class '([^']+)'>", r"type[\1]", t)  # ty class objects
    t = re.sub(r"TypedDict\('(?:[\w.]+\.)?(\w+)', \{.*\}\)", r"\1", t)  # mypy TypedDict display
    t = re.sub(r"`-\d+", "", t)  # old mypy type-var ids
    t = re.sub(r"(\b[A-Za-z_]\w*)@[\w.<>]+", r"\1", t)  # ty / pyright T@scope
    mods = list(_STRIP_MODULES)
    if module:
        mods.append(module + ".")
    for mod in mods:
        t = re.sub(r"(?<![\w.])" + re.escape(mod), "", t)
    if t.startswith(("def ", "def(", "Overload(", "(", "bound method ")) and "->" in t:
        flags.add("opaque")
        t = _canon_signature(t)
    return t, flags


def _canon_signature(t: str) -> str:
    """Cosmetic canonicalisation of callable displays so that e.g. mypy ``def (url: str, *, timeout: float =) -> bytes``
    and ty ``(url: str, *, timeout: float = ...) -> bytes`` compare equal. Still opaque (never structurally compared)."""
    if t.startswith("Overload("):
        return re.sub(r"\s+", " ", t)
    t = re.sub(r"^bound method [\w.]+(?=\()", "", t)  # ty: bound method C.m(...) -> R
    t = re.sub(r"^def\s*[\w.]*\s*(?=\()", "", t)  # mypy: def (...), ty: def f(...)
    t = re.sub(r"\s*=\s*(?:\.\.\.|[^,()\[\]]+)?(?=\s*[,)])", "=", t)  # default values -> '='
    t = re.sub(r",\s*/(?=\s*[,)])", "", t)  # positional-only markers
    t = re.sub(r"\(\s*/\s*,?\s*", "(", t)
    return re.sub(r"\s+", " ", t).strip()


def _canon(node: TNode) -> TNode:
    if node.kind == "name":
        bare = node.name.rsplit(".", 1)[-1] if "." in node.name and node.name != "..." else node.name
        name = _ALIASES.get(bare, bare)  # module qualifiers differ by tool (_asyncio.Task vs Task)
        args = [_canon(a) for a in node.args]
        if name == "Optional" and len(args) == 1:
            return _canon(TNode("union", args=[args[0], TNode("name", name="None")]))
        if name == "Union":
            return _canon(TNode("union", args=args))
        if name == "Literal":
            lits = [TNode("literal", name=_lit_text(a)) for a in args]
            return lits[0] if len(lits) == 1 else _canon(TNode("union", args=lits))
        return TNode("name", name=name, args=args, flags=set(node.flags))
    if node.kind in ("union", "inter"):
        flat: list[TNode] = []
        for a in (_canon(x) for x in node.args):
            if a.kind == node.kind:
                flat.extend(a.args)
            else:
                flat.append(a)
        uniq = {a.render(): a for a in flat}
        keys = sorted(uniq, key=lambda k: (k == "None", k))
        items = [uniq[k] for k in keys]
        return items[0] if len(items) == 1 else TNode(node.kind, args=items)
    if node.kind == "neg":
        return TNode("neg", args=[_canon(node.args[0])])
    return node


def _lit_text(node: TNode) -> str:
    text = node.render()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
        body = text[1:-1].replace('\\"', '"').replace("\\'", "'")
        return '"' + body.replace('"', '\\"') + '"'
    return text


def normalize(raw: str | None, module: str = "") -> NormType | None:
    if raw is None:
        return None
    text, flags = _pre(raw, module)
    if "opaque" in flags:
        return NormType(raw, re.sub(r"\s+", " ", text), None, flags)
    try:
        node = _canon(_Parser(text).parse())
    except (ValueError, IndexError):
        return NormType(raw, re.sub(r"\s+", " ", text), None, flags | {"opaque"})
    names = {n.name for n in node.walk() if n.kind == "name"}
    if names & GRADUAL_NAMES:
        flags.add("gradual")
    return NormType(raw, node.render(), node, flags)


# --------------------------------------------------------------------------- relation


def _members(node: TNode) -> list[TNode]:
    return node.args if node.kind == "union" else [node]


def _widen(node: TNode) -> str:
    """Literal[1] -> int, Literal[Color.RED] -> Color, others unchanged."""
    if node.kind != "literal":
        return node.render()
    v = node.name
    if v in ("True", "False"):
        return "bool"
    if v.startswith(('"', "'")):
        return "str"
    if v.startswith(("b'", 'b"')):
        return "bytes"
    if re.fullmatch(r"-?\d+", v):
        return "int"
    if "." in v:
        return v.rsplit(".", 1)[0]
    return node.render()


def _refines(a: TNode, b: TNode) -> bool:
    """Conservative structural check that every member of ``a`` is covered by ``b``."""
    bm = {m.render() for m in _members(b)}
    if "object" in bm:
        return True
    for m in _members(a):
        r = m.render()
        if r in bm:
            continue
        if m.kind == "literal" and (_widen(m) in bm or (_widen(m) == "bool" and "int" in bm)):
            continue
        if r == "bool" and "int" in bm:
            continue
        if r == "int" and "float" in bm:
            continue  # numeric promotion (typing spec, special-types)
        if m.kind == "name" and m.name in _RUNTIME_SUBCLASS:
            base = _RUNTIME_SUBCLASS[m.name]
            if any(x.kind == "name" and x.name == base and x.args == m.args or
                   (x.kind == "name" and x.name == base and [p.render() for p in x.args] == [p.render() for p in m.args])
                   for x in _members(b)):
                continue  # ty reveals the concrete runtime class (CoroutineType) where mypy shows the ABC (Coroutine)
        if r in ("int", "float") and "complex" in bm:
            continue
        if m.kind == "name" and m.args:
            same = [x for x in _members(b) if x.kind == "name" and x.name == m.name and len(x.args) == len(m.args)]
            if any(all(_refines(p, q) for p, q in zip(m.args, x.args)) for x in same) and m.name == "tuple":
                continue  # tuple is covariant; other generics may be invariant -> not a refinement
        return False
    return True


def _is_gradual_atom(n: TNode) -> bool:
    return n.kind == "name" and n.name in GRADUAL_NAMES and not n.args


def gradual_diff(a: TNode, b: TNode) -> str:
    """Where do two types differ?

    'equal'      identical
    'both'       every difference is gradual-vs-gradual (mypy Any vs ty Unknown)
    'one'        differences only where exactly one side is gradual (list[Any] vs list[int], int | Unknown vs int)
    'structural' at least one difference between two non-gradual types (Coroutine vs CoroutineType)
    """
    if a.render() == b.render():
        return "equal"
    ga, gb = _is_gradual_atom(a), _is_gradual_atom(b)
    if ga and gb:
        return "both"
    if ga or gb:
        return "one"
    if a.kind == b.kind == "name" and a.name == b.name and len(a.args) == len(b.args):
        return _combine([gradual_diff(x, y) for x, y in zip(a.args, b.args)])
    if a.kind == b.kind and a.kind in ("union", "inter"):
        ma, mb = {m.render(): m for m in a.args}, {m.render(): m for m in b.args}
        only = [ma[k] for k in ma if k not in mb] + [mb[k] for k in mb if k not in ma]
        if only and all(_is_gradual_atom(m) for m in only):
            return "both" if any(k not in mb for k in ma) and any(k not in ma for k in mb) else "one"
        return "structural"
    if "union" in (a.kind, b.kind):  # X vs X | Unknown
        u, other = (a, b) if a.kind == "union" else (b, a)
        rest = [m for m in u.args if m.render() != other.render()]
        if len(rest) < len(u.args) and all(_is_gradual_atom(m) for m in rest):
            return "one"
    return "structural"


def _combine(kinds: list[str]) -> str:
    for k in ("structural", "one", "both"):
        if k in kinds:
            return k
    return "equal"


def relation(a: NormType | None, b: NormType | None) -> Relation:
    if a is None or b is None:
        return Relation.UNCOMPARABLE
    if "todo" in a.flags or "todo" in b.flags:
        return Relation.TODO
    if a.text == b.text:
        if (a.flags ^ b.flags) & {"exact_float", "mypy_inferred_literal", "mypy_inferred"}:
            return Relation.COSMETIC
        return Relation.EQUAL
    if not a.comparable or not b.comparable:
        return Relation.UNCOMPARABLE
    if ("gradual" in a.flags or "gradual" in b.flags) and gradual_diff(a.node, b.node) in ("both", "one"):
        return Relation.GRADUAL
    ab, ba = _refines(a.node, b.node), _refines(b.node, a.node)
    if ab and ba:
        return Relation.COSMETIC
    if ab:
        return Relation.PRECISION_A
    if ba:
        return Relation.PRECISION_B
    return Relation.DIFFERENT


def is_literal_widening(narrow: NormType, wide: NormType) -> bool:
    """True if ``narrow`` only differs from ``wide`` by keeping Literal types (``Literal[1]`` vs ``int``)."""
    if not (narrow.node and wide.node):
        return False
    widened = sorted({_widen(m) for m in _members(narrow.node)})
    return widened == sorted(m.render() for m in _members(wide.node)) and any(
        m.kind == "literal" for m in _members(narrow.node)
    )


def is_join_vs_union(join_side: NormType, union_side: NormType, typevars: set[str] = frozenset()) -> bool:
    """mypy joins (``list[object]``, ``list[Base]``) where ty/pyright build unions (``list[A | B]``).

    Deliberately narrow: the union must contain no gradual member and the join must be ``object`` or a
    concrete class - never a type variable (``A[T]`` vs ``A[T | Unknown]`` is an inference bug, ty#4296)."""
    a, b = join_side.node, union_side.node
    if a is None or b is None or "gradual" in union_side.flags:
        return False

    def joinish(x: TNode, y: TNode) -> bool:
        if y.kind != "union" or any(_is_gradual_atom(m) for m in y.args):
            return False
        if x.render() == "object":
            return True
        return x.kind == "name" and not x.args and x.name not in typevars and x.name not in GRADUAL_NAMES and (
            x.name not in {m.render() for m in y.args})

    if a.kind != "name" or b.kind != "name" or a.name != b.name or len(a.args) != len(b.args):
        return a.render() == "object" and b.kind == "union" and not any(_is_gradual_atom(m) for m in b.args)
    diffs = [(x, y) for x, y in zip(a.args, b.args) if x.render() != y.render()]
    return bool(diffs) and all(joinish(x, y) for x, y in diffs)
