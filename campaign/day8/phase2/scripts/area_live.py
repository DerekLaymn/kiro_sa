"""Day 8 morning: live findings of the Day-7 run per feature area, before and after the Day-8 KB.

usage: area_live.py BEFORE_RUN AFTER_RUN GEN_ROOT [AREA ...]
BEFORE_RUN  = runs/day7/out            (Day-7 judge run)
AFTER_RUN   = runs/day8/day7replay-it2 (same reports replayed with the Day-8 KB, --rerun-runtime)
Prints a per-area table (programs, live before, live after, dismissed after) and, for the named AREAs,
every live finding of AFTER_RUN with kind, statement, tool messages and CPython evidence."""
import collections
import json
import sys
from pathlib import Path

before, after, gen = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
want = sys.argv[4:]


def area_of(r):
    org = next((x[7:] for x in r.get("notes", []) if x.startswith("origin=")), "")
    path = org.replace("seed ", "")
    i = path.find(gen.rstrip("/") + "/")
    parts = path[i + len(gen.rstrip("/")) + 1:].split("/") if i >= 0 else []
    return (parts[0] if parts else "?"), Path(path).name


def load(run):
    out = {}
    for f in sorted(run.glob("seed-*.json")):
        r = json.loads(f.read_text())
        out[f.stem] = r
    return out


b, a = load(before), load(after)
tab = collections.defaultdict(collections.Counter)
for stem, r in a.items():
    area, _ = area_of(r)
    c = tab[area]
    c["programs"] += 1
    rb = b.get(stem)
    if rb:
        c["live_before"] += sum(1 for fi in rb["findings"] if fi["tier"] != "dismissed")
    for fi in r["findings"]:
        if fi["tier"] == "dismissed":
            c["dismissed_after"] += 1
        else:
            c["live_after"] += 1
            if any(e["strength"] == "strong" and "bug" in str(e["supports"]) for e in fi["evidence"]):
                c["live_strong_after"] += 1
print("%-24s %5s %6s %6s %6s %6s" % ("area", "progs", "liveB", "liveA", "dismA", "strong"))
for k, c in sorted(tab.items()):
    print("%-24s %5d %6d %6d %6d %6d" % (k, c["programs"], c["live_before"], c["live_after"],
                                        c["dismissed_after"], c["live_strong_after"]))

for stem, r in a.items():
    area, name = area_of(r)
    if want and area not in want:
        continue
    if not want:
        break
    ds = {d["id"]: d for d in r["discrepancies"]}
    for fi in r["findings"]:
        if fi["tier"] == "dismissed":
            continue
        d = ds.get(fi["discrepancy_id"])
        if d is None:
            print(f"\n## {area} {stem} {name} CRASH {fi['discrepancy_id']}")
            continue
        ev = [f"{e['type']}/{e['strength']}/{e['supports']}" for e in fi["evidence"]]
        print(f"\n## {area} {stem} {name} {d['id']} {d['kind']} L{d['anchor']} {d['statement'][:90]!r}")
        print(f"   verdict={fi['verdict']} by={fi['decided_by']} ev={ev}")
        for t in ("mypy", "ty", "pyright"):
            for x in d[t][:2]:
                print("   ", t, x.get("code"), (x.get("message") or x.get("revealed_type") or "")[:160].replace("\n", " "))
