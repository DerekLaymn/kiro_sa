"""Dump distinct (relation, mypy, ty, pyright) revealed-type triples of live reveal_mismatch findings (tuning set)."""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

run, split, rel = sys.argv[1], sys.argv[2], sys.argv[3]
hold = {x for x in Path(split, "holdout.txt").read_text().split("\n") if x}
cnt = Counter()
ex = defaultdict(list)
for f in sorted(Path(run).glob("seed-*.json")):
    r = json.loads(f.read_text())
    o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    if o in hold:
        continue
    ds = {d["id"]: d for d in r["discrepancies"]}
    for x in r["findings"]:
        d = ds.get(x["discrepancy_id"])
        if x["tier"] == "dismissed" or d is None or d["kind"] != "reveal_mismatch" or d.get("reveal_relation") != rel:
            continue
        m = d["mypy"][0]["revealed_type"] if d["mypy"] else None
        t = d["ty"][0]["revealed_type"] if d["ty"] else None
        p = d["pyright"][0]["revealed_type"] if d["pyright"] else None
        key = (m, t, p)
        cnt[key] += 1
        if len(ex[key]) < 2:
            ex[key].append(f"{Path(o).name}:L{d['anchor']}")
print("total", sum(cnt.values()), "distinct", len(cnt))
for k, n in cnt.most_common(int(sys.argv[4]) if len(sys.argv) > 4 else 400):
    print(n, "| mypy:", k[0], "| ty:", k[1], "| pyright:", k[2], "|", ex[k][0])
