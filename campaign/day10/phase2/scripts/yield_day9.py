"""Day 10 morning: yield of the Day-9 programs on the DAY-10 KB (runs/day10/replay/day9, the phase-1 replay of
runs/day9/out), per group, per parent and per area. Adapted from campaign/day9/phase7/group_yield.py and
campaign/day9/phase5/parent_yield.py. Group = subdirectory of runs/day9/parents holding the mutant's parent
(campaign/day9/mk_groups.sh); programs without `__mut` in the name are `fresh`.
Columns: programs, programs with a live finding, live findings, live without only_pyright, strong live, dismissed, crashes.
A parent or group with 0 live only rediscovers known or closed families.
usage: yield_day9.py [REPLAY_DIR]  (default runs/day10/replay/day9)"""
import collections
import glob
import json
import os
import sys

R = "/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/"
OUT = R + (sys.argv[1] if len(sys.argv) > 1 else "runs/day10/replay/day9")
parent2group = {}
for g in sorted(os.listdir(R + "runs/day9/parents")):
    for f in os.listdir(R + "runs/day9/parents/" + g):
        parent2group[f[:-3]] = g
hits = {os.path.basename(p)[:-3] for p in glob.glob(R + "runs/hits/*.py")}
dropped = {os.path.basename(p)[:-3] for p in glob.glob(R + "runs/hits-dropped/*.py")}
groups, parents, areas = (collections.defaultdict(collections.Counter) for _ in range(3))
total = collections.Counter()
for f in sorted(glob.glob(OUT + "/seed-*.json")):
    d = json.load(open(f))
    org = [x for x in d["notes"] if x.startswith("origin=")]
    path = (org[0][7:] if org else "").replace("seed ", "")
    parts = path.split("/")
    area = parts[3] if path.startswith("runs/day9/gen/") else "?"
    base = os.path.basename(path)
    parent = base.split("__mut")[0] if "__mut" in base else "fresh"
    group = "fresh" if parent == "fresh" else parent2group.get(parent, "UNMAPPED:" + parent)
    kind_of = {x["id"]: x["kind"] for x in d["discrepancies"]}
    live = [fi for fi in d["findings"] if fi["dismissal"] is None]
    dis = [fi for fi in d["findings"] if fi["dismissal"] is not None]
    strong = [fi for fi in live if any(e["strength"] == "strong" and "bug" in str(e["supports"]) for e in fi["evidence"])]
    wo = [fi for fi in live if kind_of.get(fi["discrepancy_id"]) != "only_pyright"]
    for c in (groups[group], parents[parent], areas[area], total):
        c["programs"] += 1
        c["with_live"] += 1 if live else 0
        c["live"] += len(live)
        c["live_wo_pyright"] += len(wo)
        c["strong"] += len(strong)
        c["dismissed"] += len(dis)
        c["crashes"] += len(d.get("crashes") or [])
cols = ["programs", "with_live", "live", "live_wo_pyright", "strong", "dismissed", "crashes"]


def show(title, rows, where=None):
    print(title)
    print("  %-62s %-8s" % ("name", "where") + " ".join(c[:10].rjust(10) for c in cols))
    for k, c in sorted(rows.items(), key=lambda kv: (-kv[1]["live"], kv[0])):
        w = where(k) if where else ""
        print("  %-62s %-8s" % (k[:62], w) + " ".join(str(c[x]).rjust(10) for x in cols))


show("per group:", groups)
show("per parent / fresh:", parents,
     lambda p: "fresh" if p == "fresh" else "hits" if p in hits else "DROPPED" if p in dropped else "other")
show("per area dir:", areas)
show("total:", {"ALL": total})
