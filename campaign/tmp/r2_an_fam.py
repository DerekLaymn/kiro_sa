"""Round 2: live findings by (kind/relation, mdtest file family) for the tuning set. usage: run split which [kind-prefix]"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

run, split, which = sys.argv[1:4]
want = sys.argv[4] if len(sys.argv) > 4 else ""
hold = {x for x in Path(split, "holdout.txt").read_text().split("\n") if x}
cnt = Counter()
ex = {}
for f in sorted(Path(run).glob("seed-*.json")):
    r = json.loads(f.read_text())
    o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    if (which == "tuning") == (o in hold):
        continue
    name = Path(o).name
    fam = re.sub(r"__\d+\.py$", "", name).removesuffix(".py")
    ds = {d["id"]: d for d in r["discrepancies"]}
    for x in r["findings"]:
        d = ds.get(x["discrepancy_id"])
        if x["tier"] == "dismissed" or d is None:
            continue
        key = d["kind"] + ("/" + (d.get("reveal_relation") or "") if d["kind"] == "reveal_mismatch" else "")
        if want and not key.startswith(want):
            continue
        cnt[(key, fam)] += 1
        ex.setdefault((key, fam), f"{name}:L{d['anchor']}")
for k, n in sorted(cnt.items(), key=lambda kv: -kv[1])[:int(sys.argv[5]) if len(sys.argv) > 5 else 40]:
    print(n, k, ex[k])
