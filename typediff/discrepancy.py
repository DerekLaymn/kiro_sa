"""Turn normalised diagnostics into a list of per-statement discrepancies."""

from __future__ import annotations

from collections import defaultdict

from .anchors import AnchorMap
from .concerns import same_concern
from .features import tags_for_nodes
from .models import Diagnostic, Discrepancy, DiscrepancyKind, RuntimeResult, Severity, Tool
from .parsers import classify_exception
from .typenorm import Relation, normalize, relation

# Diagnostics that describe the *test harness* rather than the program under test.
META_CODES = {"undefined-reveal", "revealed-type"}

_REL_NAMES = {
    Relation.PRECISION_A: "mypy_more_precise",
    Relation.PRECISION_B: "ty_more_precise",
}


def rel_name(rel: Relation) -> str:
    return _REL_NAMES.get(rel, rel.value)


def attach_anchors(diags: dict[Tool, list[Diagnostic]], amap: AnchorMap) -> None:
    for lst in diags.values():
        for d in lst:
            d.anchor = amap.anchor(d.line)


def _problems(diags: list[Diagnostic], anchor: int) -> list[Diagnostic]:
    return [d for d in diags if d.is_problem and d.anchor == anchor and (d.code or "") not in META_CODES]


def find_discrepancies(
    diags: dict[Tool, list[Diagnostic]], amap: AnchorMap, runtime: RuntimeResult, module: str = "case"
) -> list[Discrepancy]:
    attach_anchors(diags, amap)
    mypy, ty = diags.get(Tool.MYPY, []), diags.get(Tool.TY, [])
    pyright = diags.get(Tool.PYRIGHT, [])
    out: list[Discrepancy] = []

    def new(kind: DiscrepancyKind, anchor: int, m: list[Diagnostic], t: list[Diagnostic], rel: str | None = None) -> Discrepancy:
        lo, hi = amap.span(anchor)
        st = amap.stmt(anchor)
        nodes = amap.enclosing_nodes(anchor)
        d = Discrepancy(
            id=f"D{len(out) + 1}", kind=kind, anchor=lo, anchor_end=hi,
            statement=st.text if st else (amap.lines[anchor - 1].strip() if 0 < anchor <= len(amap.lines) else ""),
            scope=amap.scope(anchor), mypy=m, ty=t,
            pyright=[p for p in pyright if p.anchor == lo and (p.is_problem or p.revealed_type is not None)],
            reveal_relation=rel,
            features=sorted(tags_for_nodes(nodes[-2:] if len(nodes) >= 2 else nodes)),
        )
        out.append(d)
        return d

    # ---------------------------------------------------------------- problems per statement
    anchors = sorted({d.anchor for d in mypy + ty if d.is_problem and (d.code or "") not in META_CODES})
    for a in anchors:
        m, t = _problems(mypy, a), _problems(ty, a)
        if m and not t:
            new(DiscrepancyKind.ONLY_MYPY, a, m, [])
            continue
        if t and not m:
            new(DiscrepancyKind.ONLY_TY, a, [], t)
            continue
        matched_m, matched_t, severity_diff = set(), set(), False
        for i, dm in enumerate(m):
            for j, dt in enumerate(t):
                if same_concern(dm, dt):
                    matched_m.add(i)
                    matched_t.add(j)
                    if (dm.severity == Severity.ERROR) != (dt.severity == Severity.ERROR):
                        severity_diff = True
        um = [d for i, d in enumerate(m) if i not in matched_m]
        ut = [d for j, d in enumerate(t) if j not in matched_t]
        if not matched_m:
            new(DiscrepancyKind.CONCERN_MISMATCH, a, m, t)
            continue
        if um:
            new(DiscrepancyKind.ONLY_MYPY, a, um, [])
        if ut:
            new(DiscrepancyKind.ONLY_TY, a, [], ut)
        if severity_diff and not (um or ut):
            new(DiscrepancyKind.SEVERITY_ONLY, a, m, t)

    # ---------------------------------------------------------------- reveal_type pairs
    rev_m: dict[int, list[Diagnostic]] = defaultdict(list)
    rev_t: dict[int, list[Diagnostic]] = defaultdict(list)
    for d in mypy:
        if d.revealed_type is not None:
            rev_m[d.line].append(d)
    for d in ty:
        if d.revealed_type is not None:
            rev_t[d.line].append(d)
    for line in sorted(set(rev_m) | set(rev_t)):
        ms = sorted(rev_m.get(line, []), key=lambda d: d.col or 0)
        ts = sorted(rev_t.get(line, []), key=lambda d: d.col or 0)
        for k in range(max(len(ms), len(ts))):
            dm = ms[k] if k < len(ms) else None
            dt = ts[k] if k < len(ts) else None
            if dm is None or dt is None:
                new(DiscrepancyKind.REVEAL_UNPAIRED, amap.anchor(line), [dm] if dm else [], [dt] if dt else [],
                    rel="unpaired")
                continue
            rel = relation(normalize(dm.revealed_type, module), normalize(dt.revealed_type, module))
            if rel in (Relation.EQUAL, Relation.COSMETIC):
                continue
            new(DiscrepancyKind.REVEAL_MISMATCH, amap.anchor(line), [dm], [dt], rel=rel_name(rel))

    # ---------------------------------------------------------------- runtime oracle: nobody flagged
    if runtime.status == "exception" and classify_exception(runtime.exc_type, runtime.exc_message) == "strong":
        frame_anchors = {amap.anchor(ln) for ln, _ in runtime.frames} or ({amap.anchor(runtime.exc_line)} if runtime.exc_line else set())
        flagged = {d.anchor for d in mypy + ty if d.is_problem}
        if frame_anchors and not (frame_anchors & flagged):
            inner = amap.anchor(runtime.frames[-1][0]) if runtime.frames else amap.anchor(runtime.exc_line or 1)
            new(DiscrepancyKind.RUNTIME_MISS, inner, [], [])

    for d in out:
        d.priority = _priority(d)
    return out


def _priority(d: Discrepancy) -> float:
    base = {
        DiscrepancyKind.RUNTIME_MISS: 0.8, DiscrepancyKind.ONLY_MYPY: 0.6, DiscrepancyKind.ONLY_TY: 0.6,
        DiscrepancyKind.CONCERN_MISMATCH: 0.4, DiscrepancyKind.REVEAL_MISMATCH: 0.5,
        DiscrepancyKind.REVEAL_UNPAIRED: 0.2, DiscrepancyKind.SEVERITY_ONLY: 0.05,
    }[d.kind]
    if d.kind == DiscrepancyKind.REVEAL_MISMATCH:
        base = {"different": 0.6, "uncomparable": 0.35, "gradual": 0.25, "todo": 0.1}.get(d.reveal_relation or "", 0.3)
    return base
