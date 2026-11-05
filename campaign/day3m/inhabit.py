"""Live findings with 'does NOT inhabit' runtime evidence (checker's revealed type contradicted by the runtime value)."""
import collections
import json
from pathlib import Path

RUN = Path("/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/runs/day3/replay")
rows = []
for f in sorted(RUN.glob("seed-*.json")):
    r = json.loads(f.read_text())
    ds = {d["id"]: d for d in r["discrepancies"]}
    origin = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    n = len(r["source"].strip().split("\n"))
    for x in r["findings"]:
        if x["tier"] == "dismissed" or x.get("dismissal"):
            continue
        d = ds.get(x["discrepancy_id"], {})
        for e in x.get("evidence") or []:
            if e.get("strength") == "strong" and e.get("supports") == "bug" and "NOT inhabit" in e.get("summary", ""):
                rows.append((n, f.stem, origin.split("/")[-1][:55], x["discrepancy_id"], d.get("statement", "")[:60], e["summary"][:130]))
                break
print(len(rows), "findings;", len({r[1] for r in rows}), "programs")
c = collections.Counter(r[1] for r in rows)
seen = set()
for r in sorted(rows):
    if r[1] in seen:
        continue
    seen.add(r[1])
    print(r[0], r[1], r[2], r[3], "|", r[4], "|", r[5], f"(x{c[r[1]]})")
