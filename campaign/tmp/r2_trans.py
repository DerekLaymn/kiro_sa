"""Print the individual findings behind small transitions out1 -> out2 (PRECISION-RUNTIME-CONSISTENT new, cascade lost,
disappeared)."""
import json
import sys
from pathlib import Path

a_dir, b_dir = sys.argv[1], sys.argv[2]


def load(d):
    out = {}
    for f in Path(d).glob("seed-*.json"):
        r = json.loads(f.read_text())
        ds = {x["id"]: x for x in r["discrepancies"]}
        out[f.name] = (r, ds)
    return out


A, B = load(a_dir), load(b_dir)
for name, (rb, dsb) in B.items():
    ra, dsa = A[name]
    fa = {(dsa[x["discrepancy_id"]]["kind"], dsa[x["discrepancy_id"]]["anchor"]): x for x in ra["findings"] if x["discrepancy_id"] in dsa}
    fb = {(dsb[x["discrepancy_id"]]["kind"], dsb[x["discrepancy_id"]]["anchor"]): x for x in rb["findings"] if x["discrepancy_id"] in dsb}
    lines = rb["source"].split("\n")
    for k, x in fb.items():
        if x["decided_by"] == "kb:PRECISION-RUNTIME-CONSISTENT" and (k not in fa or fa[k]["decided_by"] != x["decided_by"]):
            d = dsb[x["discrepancy_id"]]
            print("NEW PRECISION", name, "L", d["anchor"], lines[d["anchor"] - 1].strip()[:90], "| mypy:", [y.get("revealed_type") for y in d["mypy"]], "ty:", [y.get("revealed_type") for y in d["ty"]], d.get("reveal_relation"))
    for k, x in fa.items():
        if k not in fb:
            d = dsa[x["discrepancy_id"]]
            print("DISAPPEARED", name, "L", d["anchor"], x["tier"], x["decided_by"], "| mypy:", [y.get("revealed_type") for y in d["mypy"]], "ty:", [y.get("revealed_type") for y in d["ty"]])
        elif fa[k]["decided_by"].startswith("rule:cascade") and not fb[k]["decided_by"].startswith("rule:cascade"):
            d = dsa[x["discrepancy_id"]]
            print("CASCADE LOST", name, "L", d["anchor"], fb[k]["tier"], fb[k]["decided_by"])
