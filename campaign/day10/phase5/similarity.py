"""Similarity of the Day 10 strong-evidence candidates to every file in runs/hits (check_hits.py body() + difflib ratio).
Prints, per candidate, the highest ratio and the file it is closest to, and the number of hits at or above 0.80.
Also the ratio of each candidate to the other candidates (a promotion of two siblings must not make a near-duplicate pair)."""
import difflib
import re
from pathlib import Path

R = Path("/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa")
CANDS = [ln.strip() for ln in (R / "campaign/day10/phase5/candidates.txt").read_text().split("\n") if ln.strip()]


def body(src: str) -> str:
    out = [ln for ln in src.split("\n") if not re.match(r"#\s*(area|hypothesis|origin|features):", ln) and ln.strip()]
    return "\n".join(out)


hits = {f.name: body(f.read_text()) for f in sorted((R / "runs/hits").glob("*.py"))}
cb = {c: body((R / "runs/day10/gen" / c).read_text()) for c in CANDS}
for c in CANDS:
    b = cb[c]
    best = max(((difflib.SequenceMatcher(None, b, hb, autojunk=False).ratio(), n) for n, hb in hits.items()))
    n80 = sum(1 for hb in hits.values() if difflib.SequenceMatcher(None, b, hb, autojunk=False).ratio() >= 0.80)
    print(f"{best[0]:.2f} (>=0.80: {n80})  {c.split('/')[-1]}  closest: {best[1]}")
print("== candidate pairs >= 0.60")
for i, a in enumerate(CANDS):
    for b in CANDS[i + 1:]:
        r = difflib.SequenceMatcher(None, cb[a], cb[b], autojunk=False).ratio()
        if r >= 0.60:
            print(f"{r:.2f}  {a.split('/')[-1]}  ~  {b.split('/')[-1]}")
