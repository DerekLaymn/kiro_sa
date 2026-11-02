"""Round 2: live reveal_mismatch rows (tuning) where the tool that reveals Unknown/Any/contains-Unknown ALSO reports an
error on the same statement. Splits by error code and by whether CPython raised on that statement."""
import json
import re
import sys
from collections import Counter
from pathlib import Path

run, split = sys.argv[1], sys.argv[2]
which = sys.argv[3] if len(sys.argv) > 3 else "tuning"
hold = {x for x in Path(split, "holdout.txt").read_text().split("\n") if x}
cnt = Counter()
ex = {}
for f in sorted(Path(run).glob("seed-*.json")):
    r = json.loads(f.read_text())
    o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    if (which == "tuning") == (o in hold):
        continue
    rt = r["runtime"]
    ds = {d["id"]: d for d in r["discrepancies"]}
    for x in r["findings"]:
        d = ds.get(x["discrepancy_id"])
        if x["tier"] == "dismissed" or d is None or d["kind"] != "reveal_mismatch":
            continue
        raised = rt["status"] == "exception" and any(ln == d["anchor"] for ln, _ in rt["frames"])
        strong = any(e["strength"] == "strong" and e["supports"] == "bug" for e in x["evidence"])
        lo, hi = d["anchor"], d["anchor_end"]
        for tool in ("ty", "mypy"):
            lst = d[tool]
            if not lst:
                continue
            rev = lst[0].get("revealed_type") or ""
            if not re.search(r"\b(Unknown|Any)\b", rev):
                continue
            errs = [y for y in r["diagnostics"][tool]
                    if lo <= y["line"] <= hi and y.get("revealed_type") is None and y["severity"] == "error"]
            codes = ",".join(sorted({y.get("code") or "" for y in errs})) or "-"
            key = (tool, d["reveal_relation"], codes, "raised" if raised else "no-raise", "strongEv" if strong else "-")
            cnt[key] += 1
            ex.setdefault(key, f"{Path(o).name}:L{d['anchor']} rev={rev[:40]}")
for k, n in sorted(cnt.items(), key=lambda kv: -kv[1])[:40]:
    print(n, k, ex[k])
