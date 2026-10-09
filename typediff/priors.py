"""Prior upstream stance: has this (or a near-identical) behaviour already been discussed on a tracker?

Used before any CONFIRMED/CANDIDATE finding is reported or drafted (pipeline + ``report.draft_issue``). A near-match,
by signature OR by feature tags, caps the finding at REVIEW and attaches the prior stance, url and a warning to
check the BODY TEXT of the tracker (title search misses duplicates: the ty#4656 example sat in ty#1172's body).

Data: ``data/known_upstream.json``. Entries in ``entries`` that carry an optional ``stance`` and the extra list
``prior_stances`` are consulted. ``prior_stances`` entries never dismiss anything (no KB entry is built from them).

  stance   open | intended | not_planned | duplicate-of     (+ url)
  match    kinds (list of discrepancy kinds, gate), then EITHER
           signature: message (regex over diagnostic message / revealed type), codes, statement, source (regexes), OR
           tags: all listed feature tags present in the statement or program.

No network access here: searching the tracker / discuss.python.org stays a manual step (FUZZING_PLAN.md §6).
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path

from .features import program_tags
from .models import Discrepancy, Finding, Tier

PATH = Path(__file__).parent / "data" / "known_upstream.json"
STANCES = {"open", "intended", "not_planned", "duplicate-of"}
_PREFIX = "PRIOR-STANCE:"


@dataclass
class Prior:
    id: str
    stance: str
    url: str
    note: str

    def line(self) -> str:
        return f"{self.id} [{self.stance}] {self.url} - {self.note}"


def _load(path: Path = PATH) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [e for e in data.get("entries", []) if e.get("stance")] + list(data.get("prior_stances", []))


def _matches(e: dict, source: str, d: Discrepancy, tags: set[str]) -> bool:
    kinds = e.get("kinds") or ([e["kind"]] if e.get("kind") else [])
    if kinds and d.kind.value not in kinds:
        return False
    if e.get("tags") and set(e["tags"]) <= tags:
        return True
    if not (e.get("message") or e.get("codes")):
        return False
    diags = d.mypy + d.ty + d.pyright
    hit = [x for x in diags if (not e.get("codes") or (x.code or "") in e["codes"])
           and re.search(e.get("message", ""), f"{x.message} {x.revealed_type or ''}")]
    return (bool(hit) and (not e.get("statement") or bool(re.search(e["statement"], d.statement)))
            and (not e.get("source") or bool(re.search(e["source"], source))))


def find_priors(source: str, d: Discrepancy | None, path: Path = PATH) -> list[Prior]:
    """Prior stances that match ``d`` by signature or by feature tags (empty for crashes: no discrepancy)."""
    if d is None:
        return []
    try:
        tags = set(d.features) | program_tags(ast.parse(source))
    except SyntaxError:
        tags = set(d.features)
    return [Prior(e["id"], e["stance"], e.get("url", ""), e.get("note", "")) for e in _load(path)
            if e.get("stance") in STANCES and _matches(e, source, d, tags)]


def warning_text(priors: list[Prior]) -> str:
    return ("Prior upstream stance found; this may already be known, intended or declined. "
            "Check the body text of the tracker (and discuss.python.org) before filing:\n"
            + "\n".join(f"- {p.line()}" for p in priors))


def apply_prior_cap(f: Finding, priors: list[Prior]) -> bool:
    """Cap a CONFIRMED/CANDIDATE finding at REVIEW and record the prior stance. Idempotent. Never raises a tier."""
    if not priors:
        return False
    if f.tier in (Tier.CONFIRMED, Tier.CANDIDATE):
        f.tier = Tier.REVIEW
    note = _PREFIX + " " + "; ".join(p.line() for p in priors) + " | check the body text on the tracker before filing"
    if note not in f.review_notes:
        f.review_notes.append(note)
    return True
