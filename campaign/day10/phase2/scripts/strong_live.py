"""Day 10 morning: list every live finding of the Day-9 programs on the Day-10 KB (runs/day10/replay/day9) with strong bug
evidence (and the programs holding them). Read-only. Same as campaign/day9/phase5/strong_live.py with the replay as input.
Prints per finding: json name, program path (below runs/day9/gen), discrepancy id and kind, strong evidence rows."""
import glob
import os

import json

R = "/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/"
OUT = R + "runs/day10/replay/day9"
progs = set()
n = 0
for f in sorted(glob.glob(OUT + "/seed-*.json")):
    d = json.load(open(f))
    org = [x for x in d["notes"] if x.startswith("origin=")]
    path = (org[0][7:] if org else "").replace("seed ", "")
    kind_of = {x["id"]: x["kind"] for x in d["discrepancies"]}
    live = [fi for fi in d["findings"] if fi["dismissal"] is None]
    strong = [fi for fi in live if any(e["strength"] == "strong" and "bug" in str(e["supports"]) for e in fi["evidence"])]
    for fi in strong:
        n += 1
        progs.add(path)
        ev = [e for e in fi["evidence"] if e["strength"] == "strong" and "bug" in str(e["supports"])]
        print(os.path.basename(f)[:-5], path[len("runs/day9/gen/"):], fi["discrepancy_id"], kind_of.get(fi["discrepancy_id"]))
        for e in ev:
            print("    ", e.get("kind"), str(e.get("text", e))[:200].replace("\n", " "))
print("strong live findings:", n, "programs:", len(progs))
