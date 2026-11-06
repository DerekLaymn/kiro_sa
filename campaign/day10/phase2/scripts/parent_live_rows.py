"""Day 10 morning: the live rows of the Day-9 mutants of the named parents (Day-10-KB replay), one line per row:
program, kind, anchor statement and the first message of each tool, so a parent whose live rows are all one known family
(a rediscovery) can be told from one that still gives new shapes.
usage: parent_live_rows.py PARENT [PARENT ...]   (substring of the parent name; reads runs/day10/replay/day9)"""
import collections
import glob
import json
import os
import re
import sys

R = "/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/"
want = sys.argv[1:]


def sh(items):
    out = []
    for y in items:
        if y.get("revealed_type"):
            out.append("reveal " + str(y["revealed_type"]))
        else:
            out.append("[%s] %s" % (y.get("code"), y["message"]))
    return "; ".join(out)[:110] or "-"


for w in want:
    print("=====", w)
    tally = collections.Counter()
    for f in sorted(glob.glob(R + "runs/day10/replay/day9/seed-*.json")):
        d = json.load(open(f))
        origin = next((x[7:] for x in d["notes"] if x.startswith("origin=")), "").replace("seed ", "")
        base = os.path.basename(origin)
        if "__mut" not in base or base.split("__mut")[0] != w:
            continue
        ds = {x["id"]: x for x in d["discrepancies"]}
        for fi in d["findings"]:
            if fi["dismissal"] is not None:
                continue
            x = ds.get(fi["discrepancy_id"])
            if not x:
                continue
            msg = sh(x["mypy"]) if x["kind"] in ("only_mypy",) else sh(x["ty"]) if x["kind"] == "only_ty" else \
                sh(x["pyright"]) if x["kind"] == "only_pyright" else "mypy: " + sh(x["mypy"]) + " | ty: " + sh(x["ty"])
            msg = re.sub(r"`[^`]*`|\"[^\"]*\"|\d+", "_", msg)
            tally[(x["kind"], msg[:140])] += 1
    for (k, m), n in tally.most_common():
        print("  %2d %-14s %s" % (n, k, m))
