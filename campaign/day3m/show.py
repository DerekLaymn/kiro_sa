"""Print source + live findings of given replay report ids: python show.py seed-xxxx seed-yyyy ..."""
import json
import sys
from pathlib import Path

RUN = Path("/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/runs/day3/replay")
for sid in sys.argv[1:]:
    r = json.loads((RUN / f"{sid}.json").read_text())
    origin = next((n for n in r["notes"] if n.startswith("origin=")), "")
    print("=" * 100)
    print(sid, origin, [n for n in r["notes"] if n.startswith("area=")])
    print(r["source"])
    print("-- runtime:", r["runtime"].get("status"), r["runtime"].get("exc_type"), (r["runtime"].get("exc_message") or "")[:150], "line", r["runtime"].get("exc_line"))
    ds = {d["id"]: d for d in r["discrepancies"]}
    for x in r["findings"]:
        if x["tier"] == "dismissed" or x.get("dismissal"):
            continue
        d = ds.get(x["discrepancy_id"], {})
        print(f"-- live {x['discrepancy_id']} {d.get('kind')} L{d.get('anchor')} {d.get('statement', '')[:80]}")
        for t in ("mypy", "ty", "pyright"):
            for m in (d.get(t) or [])[:2]:
                print(f"     {t}: {str(m)[:200]}")
    for c in (r.get("crashes") or [])[:3]:
        print("-- crash:", str(c)[:300])
