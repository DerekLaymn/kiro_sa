"""JSONL discrepancy dataset with root-cause signatures for deduplication."""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

from .models import CaseReport, Discrepancy, Finding, Tier, to_jsonable


def message_template(msg: str) -> str:
    t = re.sub(r"`[^`]*`|\"[^\"]*\"|'[^']*'", "_", msg)
    t = re.sub(r"\d+", "N", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def signature(f: Finding, d: Discrepancy | None) -> str:
    if f.signature:  # crashes already carry a stable one
        return f.signature
    codes = sorted({x.code or "" for x in (d.mypy + d.ty if d else [])})
    msgs = sorted({message_template(x.message) for x in ((d.ty if f.faulty_tool == "ty" else d.mypy) if d else [])})
    feats = sorted(d.features) if d else []
    raw = json.dumps([f.faulty_tool, f.symptom.value if f.symptom else None, d.kind.value if d else None, codes, msgs, feats])
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class Dataset:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._sigs: dict[str, str] = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("signature") and rec.get("tier") in ("confirmed", "candidate", "review"):
                    self._sigs.setdefault(rec["signature"], rec["record_id"])

    def known_summaries(self, limit: int = 30) -> list[str]:
        out = []
        if not self.path.exists():
            return out
        for line in self.path.read_text(encoding="utf-8").splitlines()[-500:]:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("tier") in ("confirmed", "candidate"):
                out.append(f"{r['record_id']}: {r.get('faulty_tool')} {r.get('symptom')} - {r.get('statement', '')[:80]} "
                           f"[{', '.join(r.get('codes', []))}]")
        return out[-limit:]

    def duplicate_of(self, sig: str) -> str | None:
        return self._sigs.get(sig)

    def add_case(self, report: CaseReport) -> list[str]:
        by_id = {d.id: d for d in report.discrepancies}
        ids = []
        with self.path.open("a", encoding="utf-8") as fh:
            for f in report.findings:
                d = by_id.get(f.discrepancy_id)
                sig = f.signature or signature(f, d)
                rid = f"{report.case_id}:{f.discrepancy_id}"
                dup = self._sigs.get(sig)
                rec = {
                    "record_id": rid, "time": time.strftime("%Y-%m-%dT%H:%M:%S"), "case_id": report.case_id,
                    "signature": sig, "duplicate_of": dup if dup != rid else None, "tier": f.tier.value,
                    "verdict": f.verdict.value, "faulty_tool": f.faulty_tool,
                    "symptom": f.symptom.value if f.symptom else None,
                    "dismissal": f.dismissal.value if f.dismissal else None, "confidence": f.confidence,
                    "decided_by": f.decided_by, "kind": d.kind.value if d else "crash",
                    "statement": d.statement if d else "", "anchor": d.anchor if d else None,
                    "codes": sorted({x.code or "" for x in (d.mypy + d.ty if d else [])}),
                    "features": d.features if d else [], "kb_hits": d.kb_hits if d else [],
                    "reasoning": f.reasoning, "correct_behavior": f.correct_behavior,
                    "evidence": to_jsonable(f.evidence), "review_notes": f.review_notes,
                    "versions": report.tool_versions, "flags": report.flags, "target_python": report.target_python,
                    "source": report.source, "reduced_source": f.reduced_source,
                }
                fh.write(json.dumps(rec) + "\n")
                if f.tier in (Tier.CONFIRMED, Tier.CANDIDATE, Tier.REVIEW):
                    self._sigs.setdefault(sig, rid)
                ids.append(rid)
        return ids
