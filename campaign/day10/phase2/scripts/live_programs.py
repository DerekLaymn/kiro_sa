"""Day 10 morning: reserve candidates. One line per Day-9 program that has at least one live finding on the Day-10 KB
(runs/day10/replay/day9): area/file, live count, live kinds, and the first mypy / ty / pyright message or reveal of the
first live row. With a second argument the full rows of the programs whose name contains one of the arguments are printed.
usage: live_programs.py AREA [AREA ...]            one line per program of these areas
       live_programs.py --rows NAME [NAME ...]    every live row of the programs whose file name contains NAME"""
import collections
import glob
import json
import os
import sys

R = "/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/"
args = sys.argv[1:]
rows_mode = bool(args) and args[0] == "--rows"
if rows_mode:
    args = args[1:]


def sh(items):
    out = []
    for y in items:
        out.append("reveal " + str(y["revealed_type"]) if y.get("revealed_type") else "[%s] %s" % (y.get("code"), y["message"]))
    return "; ".join(out)[:120] or "-"


for f in sorted(glob.glob(R + "runs/day10/replay/day9/seed-*.json")):
    d = json.load(open(f))
    origin = next((x[7:] for x in d["notes"] if x.startswith("origin=")), "").replace("seed ", "")
    parts = origin.split("/")
    area = parts[3] if len(parts) > 4 else "?"
    name = "/".join(parts[3:])
    ds = {x["id"]: x for x in d["discrepancies"]}
    live = [fi for fi in d["findings"] if fi["dismissal"] is None and fi["discrepancy_id"] in ds]
    if not live:
        continue
    if rows_mode:
        if not any(a in name for a in args):
            continue
        print("=====", name)
        for fi in live:
            x = ds[fi["discrepancy_id"]]
            print("  %s %s L%s stmt=%r" % (x["id"], x["kind"], x["anchor"], x["statement"][:70]))
            print("     mypy:", sh(x["mypy"]))
            print("     ty:  ", sh(x["ty"]))
            print("     pyr: ", sh(x["pyright"]))
    else:
        if area not in args:
            continue
        kinds = collections.Counter(ds[fi["discrepancy_id"]]["kind"] for fi in live)
        print("%-62s %2d %s" % (name[:62], len(live), dict(kinds)))
