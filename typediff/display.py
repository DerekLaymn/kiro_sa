"""Display-only differences between the spellings of one revealed type (Day 8).

``typenorm`` reports anything it cannot parse as UNCOMPARABLE, which is the right default for callables, TypedDicts and
ParamSpecs. This module is the narrow counterpart used by the KB entry ``DISPLAY-EQUIVALENT``: it rewrites the three
printer conventions that are known to differ for the SAME type and compares the results as strings. Nothing here
parses types; if the rewritten texts differ, the pair is not display noise.

Conventions handled (each seen in the Day-6/Day-7 reports):

* ParamSpec / TypeVar scope tags: ty and pyright print ``P@__init__.args`` and ``T@f``, mypy prints ``P.args`` / ``T``.
* Callables: mypy ``def (float)`` (no ``-> None``), ``def (a: int, b: int =)`` (default value hidden),
  ``def [P, R] (f: def (int, *P.args, **P.kwargs) -> R) -> def (*P.args, **P.kwargs) -> R``; ty
  ``(float, /) -> None``, ``(a: int, b: int = 0)``, ``[**P, R](f: (int, /, *args: P.args, **kwargs: P.kwargs) -> R) ->
  ((**P) -> R)``; pyright has no ``/`` marker and no generic header.
* TypedDict: mypy expands the structure, ``TypedDict(case.Options, {'verbose'?: bool})``; ty and pyright print the class
  name, ``Options`` (``Options[str]`` for a generic TypedDict; mypy does not print the type arguments).
"""

from __future__ import annotations

import re

_MARK = "\x00"  # marks a mypy ``def (...)`` callable until its return type has been completed
_OPEN, _CLOSE = "([{", ")]}"


def _match(text: str, i: int) -> int:
    """Index of the bracket that closes the one at ``text[i]``, or -1."""
    depth = 0
    for j in range(i, len(text)):
        c = text[j]
        if c in _OPEN:
            depth += 1
        elif c in _CLOSE:
            depth -= 1
            if depth == 0:
                return j
    return -1


def _typeddict_names(text: str) -> str:
    """``TypedDict(mod.Name, {...})`` -> ``Name`` (balanced, also nested)."""
    while True:
        i = text.find("TypedDict(")
        if i < 0:
            return text
        j = _match(text, i + len("TypedDict"))
        if j < 0:
            return text
        inner = text[i + len("TypedDict("):j]
        name = inner.split(",", 1)[0].strip().rsplit(".", 1)[-1]
        text = text[:i] + name + text[j + 1:]


def _strip_type_args(text: str, names: set[str]) -> str:
    """``Name[...]`` -> ``Name`` for the given (generic TypedDict) names."""
    for n in names:
        for m in list(re.finditer(rf"(?<![\w.]){re.escape(n)}\[", text))[::-1]:
            j = _match(text, m.end() - 1)
            if j > 0:
                text = text[:m.end() - 1] + text[j + 1:]
    return text


def _drop_defaults(text: str) -> str:
    """``name: int = 0, x`` and ``name: int =, x`` -> ``name: int =, x`` (the default value is not printed by mypy)."""
    return _split_defaults(text)[0]


def _split_defaults(text: str) -> tuple[str, list[str]]:
    """The text with every default value removed (``=`` kept), and the removed values in order."""
    out, values, i = [], [], 0
    while i < len(text):
        c = text[i]
        prev, nxt = text[i - 1] if i else "", text[i + 1] if i + 1 < len(text) else ""
        if c == "=" and prev in " " and nxt in " ,)" :
            out.append("=")
            j, depth = i + 1, 0
            while j < len(text):
                if text[j] in _OPEN:
                    depth += 1
                elif text[j] in _CLOSE:
                    if depth == 0:
                        break
                    depth -= 1
                elif text[j] == "," and depth == 0:
                    break
                j += 1
            values.append(text[i + 1:j].strip())
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out), values


def defaults_match(a: str, b: str, factories: frozenset[str] | set[str] = frozenset()) -> bool:
    """Two canonical texts (``display_canon(.., defaults=True)``, ty and pyright, which both print default values) are the
    same apart from their default values, and every pair of values is equal or involves a value the printer did not
    spell out: ty prints ``...`` for a ``field(default_factory=list)`` default where pyright prints the factory name,
    and ``factories`` are the names the program passes as ``default_factory=``. Any other pair of values (``0`` vs ``1``,
    ``None`` vs ``0``) is a real difference."""
    sa, va = _split_defaults(a)
    sb, vb = _split_defaults(b)
    if sa != sb or len(va) != len(vb):
        return False
    return all(x == y or "..." in (x, y) or x in factories or y in factories for x, y in zip(va, vb))


def _complete_callables(text: str) -> str:
    """Give every mypy ``def (...)`` callable (marked) its ``-> None`` when the return type is not printed."""
    while True:
        i = text.find(_MARK)
        if i < 0:
            return text
        j = i + 1
        if j < len(text) and text[j] == "[":  # generic header: def [P, R] (...)
            k = _match(text, j)
            if k < 0:
                return text.replace(_MARK, "")
            j = k + 1
        if j >= len(text) or text[j] != "(":
            return text.replace(_MARK, "")
        k = _match(text, j)
        if k < 0:
            return text.replace(_MARK, "")
        rest = text[k + 1:]
        tail = "" if rest.lstrip().startswith("->") else " -> None"
        text = text[:i] + text[i + 1:k + 1] + tail + rest


def _is_callable_text(s: str) -> bool:
    """``(params) -> R`` or ``[T](params) -> R``."""
    j = 0
    if s[:1] == "[":
        k = _match(s, 0)
        if k < 0:
            return False
        j = k + 1
    if s[j:j + 1] != "(":
        return False
    k = _match(s, j)
    return k > 0 and s[k + 1:].lstrip().startswith("->")


def _unparen_callable_returns(text: str) -> str:
    """ty/pyright print a callable in return position in parentheses, ``-> ((**P) -> R)``, mypy does not."""
    pos = 0
    while True:
        i = text.find("-> (", pos)
        if i < 0:
            return text
        o = i + 3
        c = _match(text, o)
        if c > 0 and _is_callable_text(text[o + 1:c]):
            text = text[:o] + text[o + 1:c] + text[c + 1:]
        pos = i + 3


def _paramspec_lists(text: str) -> str:
    """A ParamSpec argument of a generic class: mypy prints ``Runner[[name: str, *, upper: bool =], str]``, ty and pyright
    ``Runner[(name: str, *, upper: bool = False), str]``. A ``[`` at the start of a type argument becomes ``(`` (and its
    closing ``]`` becomes ``)``) in every spelling."""
    chars, stack = list(text), []
    for i, c in enumerate(chars):
        if c == "[":
            before = "".join(chars[:i]).rstrip()[-1:]
            stack.append(before != "" and before in "[,")
            if stack[-1]:
                chars[i] = "("
        elif c == "]" and stack and stack.pop():
            chars[i] = ")"
    return "".join(chars)


def display_canon(text: str, module: str = "case", typeddicts: frozenset[str] | set[str] = frozenset(),
                  header: bool = True, defaults: bool = False) -> str:
    """The spelling-independent form of one revealed type (see the module docstring). Default values are dropped unless
    ``defaults`` is true (mypy does not print them; ty and pyright do, see ``defaults_match``)."""
    t = (text or "").strip()
    t = re.sub(r"@[A-Za-z_]\w*", "", t)  # scope tags
    for prefix in (module + ".", "builtins.", "typing."):
        t = re.sub(r"(?<![\w.])" + re.escape(prefix), "", t)
    t = _paramspec_lists(t)
    t = _typeddict_names(t)
    t = _strip_type_args(t, set(typeddicts))
    t = re.sub(r"\bdef (?=[(\[])", _MARK, t)
    t = re.sub(r"\]\s+\(", "](", t)
    t = re.sub(r"\*args: (\w+)\.args, \*\*kwargs: \1\.kwargs", r"**\1", t)  # ty
    t = re.sub(r"\*(\w+)\.args, \*\*\1\.kwargs", r"**\1", t)  # mypy
    t = re.sub(r",\s*/(?=[,)])", "", t)
    t = re.sub(r"\(\s*/\s*,\s*", "(", t)
    if not defaults:
        t = _drop_defaults(t)
    t = _complete_callables(t)
    t = _unparen_callable_returns(t)
    t = re.sub(r"(?<=[\[ ])\*\*(?=\w+(?:,|\]))", "", t)  # header [**P, R] -> [P, R]
    if not header:
        t = re.sub(r"^\[[^\]]*\]\s*(?=\()", "", t)
    return re.sub(r"\s+", " ", t).strip()


__all__ = ["display_canon"]
