"""How many live reveal_mismatch findings (tuning) have a gradual reveal from a tool that ALSO reported an error on that statement?"""
import json
import sys
from collections import Counter
from pathlib import Path

run, split = sys.argv[1], sys.argv[2]
hold = {x for x in Path(split, "holdout.txt").read_text().split("\n") if x}
GRAD = {"Any", "Unknown"}
cnt = Counter()
ex = {}
for f in sorted(Path(run).glob("seed-*.json")):
    r = json.loads(f.read_text())
    o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    if o in hold:
        continue
    ds = {d["id"]: d for d in r["discrepancies"]}
    for x in r["findings"]:
        d = ds.get(x["discrepancy_id"])
        if x["tier"] == "dismissed" or d is None or d["kind"] != "reveal_mismatch":
            continue
        strong = any(e["strength"] == "strong" and e["supports"] == "bug" for e in x["evidence"])
        lo, hi = d["anchor"], d["anchor_end"]
        for tool in ("mypy", "ty"):
            lst = d[tool]
            if not lst or lst[0].get("revealed_type") not in GRAD:
                continue
            errs = [y for y in r["diagnostics"][tool]
                    if lo <= y["line"] <= hi and y.get("revealed_type") is None and y["severity"] == "error"]
            key = (tool, d["reveal_relation"], "err-on-stmt" if errs else "no-err", "strong-bug-ev" if strong else "no-strong")
            cnt[key] += 1
            ex.setdefault(key, f"{Path(o).name}:L{d['anchor']}")
for k, n in sorted(cnt.items(), key=lambda kv: -kv[1]):
    print(n, k, ex[k])
