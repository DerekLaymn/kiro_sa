"""Round 3: live runtime_miss rows with `TypeError: 'X' object is not callable`: is the cause a stub-bodied callee?"""
import json
import sys
from collections import Counter
from pathlib import Path

from typediff.replay import state_from_report
from typediff.rules import _stub_callee

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
        if rt.get("exc_type") != "TypeError" or "not callable" not in (rt.get("exc_message") or ""):
            continue
        st = state_from_report(r)
        stub = _stub_callee(st, rt.get("exc_line"))
        key = (sp, rt["exc_message"][:40], "stub-callee" if stub else "no-stub")
        cnt[key] += 1
        ex.setdefault(key, []).append(f"{Path(o).name}:L{rt.get('exc_line')} {r['source'].split(chr(10))[(rt.get('exc_line') or 1) - 1].strip()[:70]} stub={stub}")
for k, v in sorted(cnt.items(), key=lambda kv: -kv[1]):
    print(v, k)
    for s in ex[k][:4]:
        print("     ", s)
