"""Similarity of the Day 8 strong-evidence candidates to every file in runs/hits (check_hits.py body() + difflib ratio).
Prints, per candidate, the highest ratio and the file it is closest to, and the number of hits at or above 0.80."""
import difflib
import re
import sys
from pathlib import Path

R = Path("/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa")
CANDS = [ln.strip() for ln in (R / "campaign/day8/phase5/candidates.txt").read_text().split("\n") if ln.strip()]


def body(src: str) -> str:
    out = [ln for ln in src.split("\n") if not re.match(r"#\s*(area|hypothesis|origin|features):", ln) and ln.strip()]
    return "\n".join(out)


hits = {f.name: body(f.read_text()) for f in sorted((R / "runs/hits").glob("*.py"))}
for c in CANDS:
    b = body((R / "runs/day8/gen" / c).read_text())
    best = max(((difflib.SequenceMatcher(None, b, hb, autojunk=False).ratio(), n) for n, hb in hits.items()))
    n80 = sum(1 for hb in hits.values() if difflib.SequenceMatcher(None, b, hb, autojunk=False).ratio() >= 0.80)
    print(f"{best[0]:.2f} (>=0.80: {n80})  {c.split('/')[-1]}  closest: {best[1]}")
