"""List what the new KB entries dismissed (distinct diagnostic messages) for manual audit."""
import json
import sys
from collections import Counter
from pathlib import Path

run = sys.argv[1]
for entry in ("kb:ASSERT-TYPE-LITERAL-RETENTION", "kb:MYPY-FIRST-ASSIGNMENT-TYPE", "kb:ANNOTATION-ONLY-READ"):
    cnt = Counter()
    progs = Counter()
    rt = Counter()
    for f in Path(run).glob("seed-*.json"):
        r = json.loads(f.read_text())
        ds = {d["id"]: d for d in r["discrepancies"]}
        o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
        for fi in r["findings"]:
            if fi["decided_by"] != entry:
                continue
            d = ds[fi["discrepancy_id"]]
            diags = d["mypy"] or d["ty"]
            msg = " || ".join(x["message"][:110] for x in diags)
            if entry == "kb:ANNOTATION-ONLY-READ":
                names = tuple(sorted({x["message"].split("`")[1] for x in d["ty"] if "`" in x["message"]}))
                msg = f"{len(names)} names {names}"
            cnt[msg] += 1
            progs[Path(o).name.rsplit("_", 1)[0]] += 1
            rt[r["runtime"]["status"] + ":" + str(r["runtime"].get("exc_type"))] += 1
    print("=====", entry, "total", sum(cnt.values()), "distinct", len(cnt))
    print("runtime:", dict(rt))
    print("by origin family:", progs.most_common(8))
    for m, n in cnt.most_common(25):
        print(" ", n, m)
