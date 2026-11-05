"""Summarise the no-LLM pipeline run over runs/hits: per program, every finding's tier / dismissal / decided_by / evidence."""
import json
import sys
from pathlib import Path

RUN = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/runs/day3/hitscheck")
rows = []
for f in sorted(RUN.glob("2026*.json")):
    r = json.loads(f.read_text())
    origin = next((n.split("=", 1)[1] for n in r["notes"] if n.startswith("origin=")), "")
    ds = {d["id"]: d for d in r["discrepancies"]}
    rt = r.get("runtime") or {}
    line = [f"## {Path(origin).name}  runtime={rt.get('status')}/{rt.get('exc_type')}  crashes={[c['signature'][:60] for c in r.get('crashes') or []]}"]
    for x in r["findings"]:
        d = ds.get(x["discrepancy_id"], {})
        ev = [f"{e['type']}/{e['strength']}/{e['supports']}" for e in x.get("evidence") or []][:3]
        line.append(f"   {x['discrepancy_id']} {d.get('kind', 'crash')} L{d.get('anchor')} tier={x['tier']} dismissal={x.get('dismissal')} by={x['decided_by']} ev={ev}")
        if x.get("dismissal") or x["tier"] == "dismissed":
            line.append(f"       reason: {x.get('reasoning', '')[:160]}")
            line.append(f"       review_notes: {[n[:110] for n in x.get('review_notes') or []]}  sig={x.get('signature')}")
    rows.append("\n".join(line))
print("\n".join(rows))
