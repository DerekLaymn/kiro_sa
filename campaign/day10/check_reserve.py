"""Day 10 morning: check the pass-2 reserve parents (runs/day10/parents/R_reserve*).
For each: the best difflib ratio of its body to any file in runs/hits (campaign/day4m/check_hits.py measure, flag >= 0.80),
to the other reserve parents, and the number of live findings its Day-9 program has in the Day-10-KB replay.
usage: check_reserve.py [REPLAY_RUN]  (default runs/day10/replay/day9)"""
import difflib
import glob
import json
import os
import re
import sys

R = "/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/"
REPLAY = R + (sys.argv[1] if len(sys.argv) > 1 else "runs/day10/replay/day9")


def body(src):
    return "\n".join(ln for ln in src.split("\n")
                     if not re.match(r"#\s*(area|hypothesis|origin|features|expected):", ln) and ln.strip())


hits = {os.path.basename(p): body(open(p).read()) for p in glob.glob(R + "runs/hits/*.py")}
live = {}
for f in glob.glob(REPLAY + "/seed-*.json"):
    d = json.load(open(f))
    org = next((x[7:] for x in d["notes"] if x.startswith("origin=")), "").replace("seed ", "")
    live[os.path.basename(org)] = sum(1 for fi in d["findings"] if fi["tier"] != "dismissed")
files = sorted(glob.glob(R + "runs/day10/parents/R_reserve*/*.py"))
bodies = {f: body(open(f).read()) for f in files}
print("%-34s %6s %-48s %6s %s" % ("reserve parent", "hits", "closest hit", "peer", "live(Day 9, Day-10 KB)"))
bad = 0
for f in files:
    b = bodies[f]
    best = max((difflib.SequenceMatcher(None, b, v, autojunk=False).ratio(), k) for k, v in hits.items())
    peer = max((difflib.SequenceMatcher(None, b, bodies[g], autojunk=False).ratio() for g in files if g != f), default=0.0)
    h = os.path.basename(f).rsplit("_", 1)[-1][:-3]
    n = next((v for k, v in live.items() if k.endswith(h + ".py")), None)
    flag = " <-- >= 0.80" if best[0] >= 0.80 or peer >= 0.80 else ""
    bad += bool(flag)
    print("%-34s %6.2f %-48s %6.2f %s%s" % (os.path.basename(f), best[0], best[1][:48], peer, n, flag))
print("parents: %d; flagged: %d" % (len(files), bad))
