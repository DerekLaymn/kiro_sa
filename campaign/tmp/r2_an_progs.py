"""Round 2: which programs / origin families carry the live reveal_mismatch rows (tuning)? usage: run split relation which"""
import json
import sys
from collections import Counter
from pathlib import Path

run, split, rel, which = sys.argv[1:5]
hold = {x for x in Path(split, "holdout.txt").read_text().split("\n") if x}
fam = Counter()
prog = Counter()
for f in sorted(Path(run).glob("seed-*.json")):
    r = json.loads(f.read_text())
    o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    if (which == "tuning") == (o in hold):
        continue
    ds = {d["id"]: d for d in r["discrepancies"]}
    for x in r["findings"]:
        d = ds.get(x["discrepancy_id"])
        if x["tier"] == "dismissed" or d is None or d["kind"] != "reveal_mismatch" or d.get("reveal_relation") != rel:
            continue
        name = Path(o).name
        fam[name.split("__")[0]] += 1
        prog[name] += 1
print(rel, which, "total", sum(fam.values()), "programs", len(prog))
print("families", fam.most_common())
for n, c in prog.most_common(25):
    print(c, n)
