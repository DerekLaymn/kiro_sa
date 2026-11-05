"""For candidate parents: does ty 0.0.97 still crash on them, and how similar are they to each hit and to each other?
Usage: python cand_sim.py CAND.py ...  (similarity = difflib ratio of header-less bodies, as in check_hits.py)"""
import difflib
import re
import subprocess
import sys
from pathlib import Path

HITS = Path("/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/runs/hits")
TY = "/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin/ty"


def body(src: str) -> str:
    return "\n".join(ln for ln in src.split("\n")
                     if not re.match(r"#\s*(area|hypothesis|origin|features):", ln) and ln.strip())


hits = {f.name: body(f.read_text()) for f in sorted(HITS.glob("*.py"))}
cands = {Path(p).name: body(Path(p).read_text()) for p in sys.argv[1:]}
for name, b in cands.items():
    r = subprocess.run([TY, "check", "--python-version", "3.13", str(next(Path(p) for p in sys.argv[1:] if Path(p).name == name))],
                       capture_output=True, text=True, timeout=90)
    best = max(((difflib.SequenceMatcher(None, b, hb, autojunk=False).ratio(), hn) for hn, hb in hits.items()))
    print(f"{name}\n   ty rc={r.returncode}  most similar hit {best[1]} {best[0]:.2f}")
names = list(cands)
print("pairwise among candidates:")
for i, a in enumerate(names):
    for c in names[i + 1:]:
        print(f"  {difflib.SequenceMatcher(None, cands[a], cands[c], autojunk=False).ratio():.2f}  {a} ~ {c}")
