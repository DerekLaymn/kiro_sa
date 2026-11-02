"""Audit of what the round-2 entries dismissed in runs/day2/out2: counts, origin families, CPython exception at the
dismissed statement, and 18 random samples per entry (seeded)."""
import ast
import json
import random
import sys
from collections import Counter
from pathlib import Path

run, split = sys.argv[1], sys.argv[2]
hold = {x for x in Path(split, "holdout.txt").read_text().split("\n") if x}
ENTRIES = ["kb:REVEAL-ERROR-RECOVERY", "kb:MYPY-13807-ALIASED-CONDITIONS", "kb:ASSERT-TYPE-LITERAL-RETENTION"]
rows = {e: [] for e in ENTRIES}
for f in sorted(Path(run).glob("seed-*.json")):
    r = json.loads(f.read_text())
    o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    ds = {d["id"]: d for d in r["discrepancies"]}
    rt = r["runtime"]
    lines = r["source"].split("\n")
    for fi in r["findings"]:
        if fi["decided_by"] in rows:
            d = ds[fi["discrepancy_id"]]
            raised = rt["status"] == "exception" and any(ln == d["anchor"] for ln, _ in rt["frames"])
            strong = any(e["strength"] == "strong" and e["supports"] == "bug" for e in fi["evidence"])
            rows[fi["decided_by"]].append((o, d, raised, strong, rt["status"] + ":" + str(rt.get("exc_type")), lines))
rnd = random.Random(7)
for e, lst in rows.items():
    fam = Counter(Path(o).name.split("__")[0] for o, *_ in lst)
    sets = Counter("holdout" if o in hold else "tuning" for o, *_ in lst)
    print("=====", e, "total", len(lst), dict(sets), "families", dict(fam.most_common(6)))
    print("  raised-at-statement:", sum(1 for x in lst if x[2]), " strong-bug-evidence:", sum(1 for x in lst if x[3]),
          " runtime:", dict(Counter(x[4] for x in lst).most_common(5)))
    # distinct ty/mypy gradual-bool-literal counts for assert-type
    if e.endswith("RETENTION"):
        bl = sum(1 for x in lst if any("Literal[True]" in (y["message"]) or "Literal[False]" in y["message"] for y in x[1]["ty"] + x[1]["mypy"]))
        pyr = sum(1 for x in lst if x[1]["pyright"])
        print("  bool-literal rows:", bl, " rows with pyright diag on statement object:", pyr)
    for o, d, raised, strong, rts, lines in rnd.sample(lst, min(18, len(lst))):
        stmt = " / ".join(l.strip() for l in lines[d["anchor"] - 1:d["anchor_end"]])[:110]
        t = d["ty"][0].get("revealed_type") or d["ty"][0]["message"] if d["ty"] else None
        m = d["mypy"][0].get("revealed_type") or d["mypy"][0]["message"] if d["mypy"] else None
        errs = [f"{y['code']}@{y['col']}" for y in (r_ for r_ in [])]
        print(f"  - {Path(o).name} L{d['anchor']} [{rts}{' RAISED' if raised else ''}] {stmt!r}\n      ty={str(t)[:70]!r} mypy={str(m)[:70]!r} rel={d.get('reveal_relation')}")
