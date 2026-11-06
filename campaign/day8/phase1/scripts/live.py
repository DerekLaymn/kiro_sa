"""List live findings of a run: python live.py RUN [substring-filter]"""
import json, sys
from pathlib import Path

run = Path(sys.argv[1])
flt = sys.argv[2] if len(sys.argv) > 2 else ""
n = 0
for f in sorted(run.glob("seed-*.json")):
    r = json.loads(f.read_text())
    org = next((x.split("=", 1)[1] for x in r.get("notes", []) if x.startswith("origin=")), "")
    if flt not in org and flt not in f.name:
        continue
    ds = {d["id"]: d for d in r["discrepancies"]}
    for fi in r["findings"]:
        if fi["tier"] == "dismissed":
            continue
        d = ds.get(fi["discrepancy_id"])
        if d is None:
            print(f.name, org, "CRASH-FINDING", fi["discrepancy_id"])
            continue
        n += 1
        tools = []
        for t in ("mypy", "ty", "pyright"):
            for x in d[t][:2]:
                tools.append(f"{t}:{x.get('code')}:{(x.get('message') or x.get('revealed_type') or '')[:90]}")
        ev = [f"{e['type']}/{e['strength']}/{e['supports']}" for e in fi["evidence"]]
        print(f"{f.stem} | {Path(org).name} | {d['id']} {d['kind']} L{d['anchor']} | {d['statement'][:80]!r} | {fi['verdict']} {fi['decided_by']} | kb={d['kb_hits']} | ev={ev}")
        for t in tools:
            print("      ", t)
print("total live", n)
