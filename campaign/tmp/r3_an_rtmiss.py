"""Round 3: live runtime_miss rows (both checkers silent, CPython raised): group by exception type + message template."""
import json
import re
import sys
from collections import Counter
from pathlib import Path

run = Path(sys.argv[1])
hold = {x for x in Path("runs/day2/split/holdout.txt").read_text().split("\n") if x}
cnt, ex = Counter(), {}
for f in sorted(run.glob("seed-*.json")):
    r = json.loads(f.read_text())
    o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    sp = "holdout" if o in hold else "tuning"
    ds = {d["id"]: d for d in r["discrepancies"]}
    for x in r["findings"]:
        d = ds.get(x["discrepancy_id"])
        if x["tier"] == "dismissed" or d is None or d["kind"] != "runtime_miss":
            continue
        rt = r["runtime"]
        msg = re.sub(r"'[^']*'", "'_'", rt.get("exc_message") or "")
        msg = re.sub(r"\d+", "n", msg)[:80]
        key = (sp, rt.get("exc_type"), msg)
        cnt[key] += 1
        stmt = r["source"].split("\n")[d["anchor"] - 1].strip()[:90]
        ex.setdefault(key, []).append(f"{Path(o).name}:L{d['anchor']} {stmt}")
for k, v in sorted(cnt.items(), key=lambda kv: -kv[1]):
    print(v, k)
    for s in ex[k][:3]:
        print("      ", s)
