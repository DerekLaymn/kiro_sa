"""Live findings per Day-8 program on the Day-9 KB replay (runs/day9/day8replay), grouped by area."""
import glob, json, os, collections, sys
R = "/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/"
run = R + "runs/day9/day8replay"
rows = []
area = collections.defaultdict(lambda: [0, 0, 0, 0])
for f in sorted(glob.glob(run + "/seed-*.json")):
    d = json.load(open(f))
    origin = next((x[7:] for x in d["notes"] if x.startswith("origin=")), "")
    kinds = {x["id"]: x["kind"] for x in d["discrepancies"]}
    live = [fi for fi in d["findings"] if fi["tier"] != "dismissed"]
    dis = [fi for fi in d["findings"] if fi["tier"] == "dismissed"]
    strong = [fi for fi in live if fi.get("strong") or fi.get("evidence_strength") == "strong"]
    path = origin.replace("seed ", "")
    a = os.path.basename(os.path.dirname(path))
    area[a][0] += 1
    area[a][1] += len(live)
    area[a][2] += len(dis)
    rows.append((a, os.path.basename(path), len(live), len(dis), sorted({kinds.get(fi.get("discrepancy_id"), "crash") for fi in live})))
print("%-26s %5s %5s %5s" % ("area(dir)", "progs", "live", "dism"))
for a, v in sorted(area.items(), key=lambda kv: -kv[1][1]):
    print("%-26s %5d %5d %5d" % (a, v[0], v[1], v[2]))
print()
if len(sys.argv) > 1:
    for r in sorted(rows):
        if r[2] > 0:
            print(r)
else:
    print(json.dumps(json.load(open(sorted(glob.glob(run + "/seed-*.json"))[0])), indent=1)[:2500])
