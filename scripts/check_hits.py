"""Validate every file in seeds/parents (the parent programs): 3-line header, AREAS key, py_compile, typediff.generator.preflight (no ERROR),
CPython run, and near-duplicate detection (difflib ratio of the bodies without the header comments)."""
import difflib
import re
import subprocess
import sys
from pathlib import Path

from typediff.generator import blocking, preflight
from typediff.strategy import AREAS

ROOT = Path(__file__).resolve().parent.parent
# Usage: python scripts/check_hits.py [THRESHOLD] [HITS_DIR]; the default directory is the committed seeds/parents.
HITS = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "seeds" / "parents"
THRESH = float(sys.argv[1]) if len(sys.argv) > 1 else 0.80


def body(src: str) -> str:
    out = [ln for ln in src.split("\n") if not re.match(r"#\s*(area|hypothesis|origin|features):", ln) and ln.strip()]
    return "\n".join(out)


files = sorted(HITS.glob("*.py"))
bad = 0
bodies = {}
for f in files:
    src = f.read_text()
    lines = src.split("\n")
    probs = []
    if not (lines[0].startswith("# area: ") and lines[1].startswith("# hypothesis: ") and lines[2].startswith("# origin: ")):
        probs.append("header")
    area = lines[0].removeprefix("# area: ").strip()
    if area not in AREAS:
        probs.append(f"area {area!r} not in AREAS")
    try:
        compile(src, str(f), "exec")
    except SyntaxError as e:
        probs.append(f"syntax {e}")
    pf = preflight(src, "3.13")
    if blocking(pf):
        probs.append(f"preflight {pf}")
    r = subprocess.run([sys.executable, "-W", "ignore", str(f)], capture_output=True, text=True, timeout=60)
    rt = "ok" if r.returncode == 0 else (r.stderr.strip().split("\n") or [""])[-1][:80]
    print(f"{f.name:70s} {area:24s} preflight={[p[:60] for p in pf]} runtime={rt}")
    if probs:
        bad += 1
        print("   PROBLEMS:", probs)
    bodies[f.name] = body(src)
print(len(files), "files;", bad, "with problems")
print(f"\nnear-duplicate pairs (difflib ratio >= {THRESH}):")
names = list(bodies)
for i, a in enumerate(names):
    for b in names[i + 1:]:
        ratio = difflib.SequenceMatcher(None, bodies[a], bodies[b], autojunk=False).ratio()
        if ratio >= THRESH:
            print(f"  {ratio:.2f}  {a}  ~  {b}")
