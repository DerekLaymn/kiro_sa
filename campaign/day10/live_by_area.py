"""Live findings and programs per `# area:` line of the program source. Usage: live_by_area.py OUT_DIR"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

progs, live, live_wo, prog_live = Counter(), Counter(), Counter(), Counter()
for f in sorted(Path(sys.argv[1]).glob("seed-*.json")):
    r = json.loads(f.read_text())
    m = re.search(r"^# area: (\S+)", r["source"], re.M)
    area = m.group(1) if m else "?"
    ds = {d["id"]: d for d in r["discrepancies"]}
    progs[area] += 1
    n = nwo = 0
    for x in r["findings"]:
        if x["tier"] == "dismissed":
            continue
        n += 1
        d = ds.get(x["discrepancy_id"])
        nwo += not d or d["kind"] != "only_pyright"
    live[area] += n
    live_wo[area] += nwo
    prog_live[area] += bool(n)
print(f"{'area':32} programs prog_with_live live live_wo_only_pyright")
for a in sorted(progs, key=lambda a: (-live[a], a)):
    print(f"{a:32} {progs[a]:8} {prog_live[a]:14} {live[a]:4} {live_wo[a]:4}")
print(f"{'TOTAL':32} {sum(progs.values()):8} {sum(prog_live.values()):14} {sum(live.values()):4} {sum(live_wo.values()):4}")
