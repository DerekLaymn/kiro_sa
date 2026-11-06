"""Day 10 preflight for the bare-name operators (plan day10-morning.md section 10): similarity of each generated mutant to
its parent (difflib ratio of the bodies without the header comments, as in campaign/day4m/check_hits.py).
A mutant with ratio >= 0.80 is a near-copy of its parent, so the operator did not change it. A group is flagged when
fewer than half of its mutants are below 0.80.
Usage: parent_similarity.py [gen_dir]
"""
import difflib
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

gen = Path(sys.argv[1] if len(sys.argv) > 1 else "runs/day10/gen")
THRESH = 0.80
ORIGIN = re.compile(r"^# origin: (runs/day10/parents/(\w+)/\S+\.py)", re.M)


def body(src: str) -> str:
    out = [ln for ln in src.split("\n") if not re.match(r"#\s*(area|hypothesis|origin|features):", ln) and ln.strip()]
    return "\n".join(out)


rows = defaultdict(list)
for p in sorted(gen.rglob("*.py")):
    src = p.read_text()
    m = ORIGIN.search(src)
    if not m:
        continue
    parent = Path(m.group(1))
    if not parent.exists():
        print("missing parent", parent, "for", p)
        continue
    rows[m.group(2)].append(difflib.SequenceMatcher(None, body(parent.read_text()), body(src)).ratio())

print(f"{'group':16} {'n':>3} {'median':>7} {'max':>5} {'<0.80':>6} {'share':>6}  flag")
for g in sorted(rows):
    r = rows[g]
    below = sum(x < THRESH for x in r)
    flag = "FLAG (fewer than half changed)" if below * 2 < len(r) else ""
    print(f"{g:16} {len(r):>3} {statistics.median(r):>7.2f} {max(r):>5.2f} {below:>6} {below/len(r):>6.0%}  {flag}")
