"""Origin oracle: compare each tool's reveal_type with the expectation the program's OWN test suite recorded.

Harvested seeds keep the expectation comments of the suite they came from:

    mypy   ``reveal_type(x)  # N: Revealed type is "builtins.int"``
    ty     ``reveal_type(x)  # revealed: int``

The checker whose suite wrote the comment is the ORIGIN tool. Its suite blessed that output, so
 * origin tool == its expectation, other tool differs  -> the difference is the other tool's (or a design) difference,
   which is what a narrow DESIGN_DIVERGENCE dismissal may use (kb.py: ORIGIN-ORACLE-REVEAL);
 * origin tool != its own expectation                  -> version skew or a broken harvest (ORIGIN-MISMATCH): a pipeline
   problem to fix in the harvester or to exclude, never a tool bug claim.

This is evidence for SORTING and EXPLAINING the queue. It never replaces CPython (the kb entry is demoted when the
runtime contradicts either tool's reveal).
"""

from __future__ import annotations

import re
from functools import lru_cache

from .typenorm import GRADUAL_NAMES, NormType, normalize

# the harvester stamps every program with its suite; only then is the comment a suite expectation
_SUITE_HEADER = {"mypy": r"^#\s*origin:\s*python/mypy\b", "ty": r"^#\s*origin:\s*ruff mdtest\b"}
_MYPY = re.compile(r'Revealed type is "(.*?)"(?=\s*(?:#|$))')
_MYPY_SQ = re.compile(r"Revealed type is '(.*?)'(?=\s*(?:#|$))")
_TY = re.compile(r"#\s*revealed:\s*(.+?)\s*$")


@lru_cache(maxsize=256)
def expectations(source: str) -> dict[int, tuple[str, tuple[str, ...]]]:
    """line -> (origin tool, expected reveal texts in source order)."""
    out: dict[int, tuple[str, tuple[str, ...]]] = {}
    for i, line in enumerate(source.split("\n"), 1):
        if "# N:" in line and "Revealed type is" in line:
            texts = _MYPY.findall(line) or _MYPY_SQ.findall(line)
            if texts:
                out[i] = ("mypy", tuple(texts))
        elif "# revealed:" in line:
            m = _TY.search(line)
            if m:
                out[i] = ("ty", (m.group(1),))
    return out


def _norm(text: str | None, module: str) -> NormType | None:
    return normalize(text, module) if text is not None else None


def same_reveal(a: str | None, b: str | None, module: str) -> bool:
    na, nb = _norm(a, module), _norm(b, module)
    return bool(na and nb and na.text == nb.text)


def status(source: str, module: str, mypy_reveals: list, ty_reveals: list) -> dict | None:
    """For a reveal discrepancy: {'origin': tool, 'expected': text, 'match': {'mypy': bool, 'ty': bool}} or None.

    ``mypy_reveals`` / ``ty_reveals`` are the tools' Diagnostic lists for this discrepancy. Only an unambiguous pairing
    (one reveal per tool on a line whose expectation comment holds exactly one text) is used."""
    if len(mypy_reveals) != 1 or len(ty_reveals) != 1:
        return None
    m, t = mypy_reveals[0], ty_reveals[0]
    if m.line != t.line or m.revealed_type is None or t.revealed_type is None:
        return None
    exp = expectations(source).get(m.line)
    if exp is None or len(exp[1]) != 1:
        return None
    origin, (expected,) = exp[0], exp[1]
    if not re.search(_SUITE_HEADER[origin], source, re.M):
        return None  # a `# revealed:` comment in someone's bug report is the reporter's observation, not a blessed expectation
    return {"origin": origin, "expected": expected,
            "match": {"mypy": same_reveal(m.revealed_type, expected, module), "ty": same_reveal(t.revealed_type, expected, module)}}


def _gradual_count(text: str, module: str) -> int:
    n = _norm(text, module)
    return sum(1 for x in n.node.walk() if x.kind == "name" and x.name in GRADUAL_NAMES) if n and n.node else 0


def _root_gradual(text: str, module: str) -> bool:
    n = _norm(text, module)
    return bool(n and n.node and n.node.kind == "name" and n.node.name in GRADUAL_NAMES and not n.node.args)


def other_is_less_precise(origin_text: str, other_text: str, module: str) -> bool:
    """The non-origin tool answered with MORE gradual (Any/Unknown) parts than the blessed answer, or with a bare
    Any/Unknown where the blessed answer is a real type."""
    if _root_gradual(other_text, module):
        return not _root_gradual(origin_text, module)
    return _gradual_count(other_text, module) > _gradual_count(origin_text, module)
