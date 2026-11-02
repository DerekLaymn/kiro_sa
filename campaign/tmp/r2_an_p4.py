"""Round 2 pattern 4: live only_mypy [assignment] (tuning). Split by pyright agreement, hints, runtime, first-assignment-ness."""
import json
import re
import sys
from collections import Counter
from pathlib import Path

run, split, kind, code = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
hold = {x for x in Path(split, "holdout.txt").read_text().split("\n") if x}
cnt = Counter()
ex = {}
for f in sorted(Path(run).glob("seed-*.json")):
    r = json.loads(f.read_text())
    o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    if o in hold:
        continue
    ds = {d["id"]: d for d in r["discrepancies"]}
    lines = r["source"].split("\n")
    rt = r["runtime"]
    for x in r["findings"]:
        d = ds.get(x["discrepancy_id"])
        if x["tier"] == "dismissed" or d is None or d["kind"] != kind:
            continue
        diags = d["mypy"] or d["ty"] or d["pyright"]
        if ",".join(sorted({y.get("code") or "" for y in diags})) != code:
            continue
        pyr = "pyright-agrees" if [y for y in d["pyright"]] else "pyright-silent"
        if not d["pyright"]:
            lo, hi = d["anchor"], d["anchor_end"]
            pyr = "pyright-agrees" if any(lo <= y["line"] <= hi and y["severity"] == "error" and y.get("revealed_type") is None
                                          for y in r["diagnostics"]["pyright"]) else "pyright-silent"
        stmt = "\n".join(lines[d["anchor"] - 1:d["anchor_end"]])
        expect = "suite-expects" if re.search(r"#\s*(E:|error|type:\s*ignore|This should (generate|be|cause))|should (generate|be an) error", stmt) else "no-expect-comment"
        hints = ",".join(h for h in d["kb_hits"] if h not in ("SUITE-EXPECTS-ERROR",)) or "-"
        raised = rt["status"] == "exception" and any(ln == d["anchor"] for ln, _ in rt["frames"])
        key = (pyr, expect, "raised" if raised else "no-raise", Path(o).name.split("__")[0], hints)
        cnt[key] += 1
        ex.setdefault(key, f"{Path(o).name}:L{d['anchor']}")
print("total", sum(cnt.values()))
for k, n in sorted(cnt.items(), key=lambda kv: -kv[1])[:45]:
    print(n, k, ex[k])
