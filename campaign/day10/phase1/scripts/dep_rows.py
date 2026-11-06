"""List every Day-9 discrepancy whose ty side is the `deprecated` rule, with its finding state."""
import glob
import json
import sys

rows = []
for f in sorted(glob.glob("runs/day9/out/*.json")):
    r = json.load(open(f))
    ds = {d["id"]: d for d in r["discrepancies"]}
    for fi in r["findings"]:
        d = ds.get(fi["discrepancy_id"])
        if not d:
            continue
        ty = d.get("ty") or []
        if any((x.get("code") == "deprecated") for x in ty):
            rows.append((f, fi, d))
print("rows", len(rows))
for f, fi, d in rows:
    print(f.split("/")[-1], d["id"], d["kind"], "decided_by=", fi.get("decided_by"), "tier=", fi.get("tier"),
          "mypy=", [x.get("code") for x in d.get("mypy") or []], "ty=", [(x.get("code"), x.get("line")) for x in d["ty"]],
          "stmt=", d.get("statement", "")[:70].replace("\n", " "), "scope=", d.get("scope"))
if rows and len(sys.argv) > 1:
    print(json.dumps(rows[0][1], indent=1)[:3000])
    print(json.dumps(rows[0][2], indent=1)[:3000])
