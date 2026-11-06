"""Count `only_pyright` discrepancies by runtime relation in a run directory and list the runtime_supports ones.
usage: only_pyright_relations.py RUN_DIR  (Day 10: same script as Days 8 and 9, which checked priority (c), runtime_supports > 0)."""
import glob
import json
import sys
from collections import Counter

run = sys.argv[1]
c, rows = Counter(), []
for f in sorted(glob.glob(run + "/seed-*.json")):
    r = json.load(open(f))
    fs = {x["discrepancy_id"]: x for x in r["findings"]}
    origin = next((n[7:] for n in r.get("notes", []) if n.startswith("origin=")), "")
    for d in r["discrepancies"]:
        if d["kind"] == "only_pyright":
            c[d["reveal_relation"]] += 1
            fi = fs[d["id"]]
            rows.append((f.split("/")[-1], d["id"], d["reveal_relation"], d["priority"], fi["tier"], fi["decided_by"],
                         d["statement"][:70], origin.split("/")[-1]))
print(run, dict(c), "total", sum(c.values()))
for r in rows:
    if r[2] == "runtime_supports":
        print("    supports:", r)
