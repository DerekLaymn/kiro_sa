"""Round 2: live reveal_mismatch rows inside programs where mypy's [assignment] error on an undeclared name was already
dismissed by MYPY-FIRST-ASSIGNMENT-TYPE (the reveal rows are the same mypy behaviour seen through reveal_type)."""
import json
import sys
from collections import Counter
from pathlib import Path

run, split, which = sys.argv[1:4]
hold = {x for x in Path(split, "holdout.txt").read_text().split("\n") if x}
cnt = Counter()
progs = set()
for f in sorted(Path(run).glob("seed-*.json")):
    r = json.loads(f.read_text())
    o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    if (which == "tuning") == (o in hold):
        continue
    fa = [x for x in r["findings"] if x["decided_by"] == "kb:MYPY-FIRST-ASSIGNMENT-TYPE"]
    if not fa:
        continue
    ds = {d["id"]: d for d in r["discrepancies"]}
    fa_lines = {ds[x["discrepancy_id"]]["anchor"] for x in fa}
    for x in r["findings"]:
        d = ds.get(x["discrepancy_id"])
        if x["tier"] == "dismissed" or d is None:
            continue
        # reveal rows after the first dismissed assignment line
        if d["kind"] == "reveal_mismatch" and d["anchor"] > min(fa_lines):
            cnt[(d["kind"], d.get("reveal_relation"))] += 1
            progs.add(Path(o).name)
        else:
            cnt[(d["kind"], "other")] += 1
print(which, "programs with a dismissed first-assignment:", len({Path(o).name for o in progs}), dict(cnt.most_common(12)))
