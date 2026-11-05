"""List live strong-evidence findings of the replay as parent candidates (small programs, non-NameError runtime evidence)."""
import json
from pathlib import Path

RUN = Path("/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/runs/day3/replay")
rows = []
for f in sorted(RUN.glob("seed-*.json")):
    r = json.loads(f.read_text())
    ds = {d["id"]: d for d in r["discrepancies"]}
    origin = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    area = next((n.split("=", 1)[1] for n in r["notes"] if n.startswith("area=")), "")
    nlines = len(r["source"].strip().split("\n"))
    rt = r.get("runtime") or {}
    exc = rt.get("exc_type")
    for x in r["findings"]:
        if x["tier"] == "dismissed" or x.get("dismissal"):
            continue
        d = ds.get(x["discrepancy_id"])
        kind = d["kind"] if d else "crash"
        strong = [e for e in (x.get("evidence") or []) if e.get("strength") == "strong" and e.get("supports") == "bug"]
        rows.append((kind, bool(strong), exc, nlines, f.name, origin, area, x["discrepancy_id"], (d or {}).get("statement", "")[:70],
                     strong[0]["summary"][:110] if strong else ""))
import collections

print("live total", len(rows), "strong", sum(1 for r in rows if r[1]))
print(collections.Counter((r[0], r[1]) for r in rows))
print()
print("== runtime_miss live (non-NameError), by size")
for r in sorted((r for r in rows if r[0] == "runtime_miss" and r[2] not in ("NameError", "UnboundLocalError")), key=lambda r: r[3]):
    print(f"{r[4]} n={r[3]} exc={r[2]} {r[6]} {r[5][-60:]} {r[7]} :: {r[8]} :: {r[9]}")
print()
print("== runtime_miss live NameError-ish count", sum(1 for r in rows if r[0] == "runtime_miss" and r[2] in ("NameError", "UnboundLocalError")))
print("== crash findings live")
for r in rows:
    if r[0] == "crash":
        print(r)
