"""Group live findings (tuning set) of a kind/relation by origin file family (name without trailing _N)."""
import json
import re
import sys
from collections import Counter
from pathlib import Path

run, split, kind = sys.argv[1], sys.argv[2], sys.argv[3]
rel = sys.argv[4] if len(sys.argv) > 4 else None
hold = {x for x in Path(split, "holdout.txt").read_text().split("\n") if x}
cnt = Counter()
for f in sorted(Path(run).glob("seed-*.json")):
    r = json.loads(f.read_text())
    o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    if o in hold:
        continue
    ds = {d["id"]: d for d in r["discrepancies"]}
    for x in r["findings"]:
        d = ds.get(x["discrepancy_id"])
        if x["tier"] == "dismissed" or d is None or d["kind"] != kind:
            continue
        if rel and d.get("reveal_relation") != rel:
            continue
        fam = re.sub(r"_\d+$", "", Path(o).stem)
        cnt[fam] += 1
print("total", sum(cnt.values()))
for k, n in cnt.most_common(40):
    print(n, k)
