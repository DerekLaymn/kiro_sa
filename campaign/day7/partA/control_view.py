import json, re
from pathlib import Path
ROOT = Path("/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa")
NEW = ("kb:UPSTREAM-TY-2171", "kb:UPSTREAM-TY-2171-ASSERT", "kb:UPSTREAM-TY-2792", "kb:UPSTREAM-TY-2792-READONLY")
out = []
n = 0
for day in ("day3", "day4", "day5"):
    for f in sorted((ROOT / f"runs/day7/ctrl-{day}").glob("seed-*.json")):
        r = json.loads(f.read_text())
        ds = {d["id"]: d for d in r["discrepancies"]}
        hits = [(fi["discrepancy_id"], fi["decided_by"]) for fi in r["findings"] if fi["decided_by"] in NEW]
        if not hits:
            continue
        old = json.loads((ROOT / f"runs/{day}/out/{f.name}").read_text())
        oldby = {fi["discrepancy_id"]: fi["decided_by"] for fi in old["findings"]}
        out.append(f"\n##### {day} {f.stem}")
        for did, by in hits:
            d = ds[did]
            n += 1
            out.append(f"  -> {did} {d['kind']} L{d['anchor']} {d['statement'][:60]!r} {by} (before: {oldby.get(did)}) rel={d.get('reveal_relation')} ty={[x['message'][:50] for x in d['ty']]} mypy={[x['message'][:50] for x in d['mypy']]}")
        for i, l in enumerate(r["source"].splitlines(), 1):
            if l.strip() and not l.startswith("#"):
                out.append(f"{i:3} {l}")
out.append(f"\nTOTAL closed rows by the new ids: {n}")
Path("/tmp/ctrl_view.txt").write_text("\n".join(out))
print(n)
