"""Validate runs/hits: 3-line header, valid AREAS key, py_compile (in memory), preflight (no ERROR), runs under CPython."""
import ast
import re
import subprocess
import sys
from pathlib import Path

from typediff.generator import blocking, preflight
from typediff.strategy import AREAS

hits = Path("/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/runs/hits")
bad = 0
for f in sorted(hits.glob("*.py")):
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
    print(f"{f.name:62s} {area:24s} preflight={[p[:50] for p in pf]} runtime={rt}")
    if probs:
        bad += 1
        print("   PROBLEMS:", probs)
print(len(list(hits.glob('*.py'))), "files;", bad, "with problems")
