"""Compare tier / dismissal / decided_by of every finding between a saved run and its replay (as day9/phase1/scripts/diff8.py)
and tally the new `decided_by` values of the findings that changed."""
import glob
import json
import os
import sys
from collections import Counter

a_dir, b_dir = sys.argv[1], sys.argv[2]
changed = total = live_a = live_b = 0
new_by = Counter()
for fa in sorted(glob.glob(a_dir + "/seed-*.json")):
    fb = os.path.join(b_dir, os.path.basename(fa))
    if not os.path.exists(fb):
        continue
    ra, rb = json.load(open(fa)), json.load(open(fb))
    A = {x["discrepancy_id"]: x for x in ra["findings"]}
    B = {x["discrepancy_id"]: x for x in rb["findings"]}
    origin = next((n for n in ra.get("notes", []) if n.startswith("origin=")), "")
    for k in sorted(set(A) | set(B)):
        a, b = A.get(k), B.get(k)
        total += 1
        ta = (a["tier"], a.get("decided_by")) if a else None
        tb = (b["tier"], b.get("decided_by")) if b else None
        live_a += bool(a and a["tier"] != "dismissed")
        live_b += bool(b and b["tier"] != "dismissed")
        if ta != tb:
            changed += 1
            new_by[tb[1] if tb else None] += 1
            print(os.path.basename(fa), k, origin[-90:], "\n   ", ta, "->", tb)
print("compared", total, "changed", changed, "live before", live_a, "live after", live_b)
print("new decided_by of changed findings:", dict(new_by))
