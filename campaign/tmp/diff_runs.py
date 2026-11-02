"""Transitions of findings between two runs of the same corpus (matched by case, kind, anchor, first message)."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

a_dir, b_dir, split = sys.argv[1], sys.argv[2], sys.argv[3]
hold = {x for x in Path(split, "holdout.txt").read_text().split("\n") if x}


def load(d):
    out = {}
    for f in Path(d).glob("seed-*.json"):
        r = json.loads(f.read_text())
        o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
        ds = {x["id"]: x for x in r["discrepancies"]}
        for fi in r["findings"]:
            x = ds.get(fi["discrepancy_id"])
            if x is None:
                key = (r["case_id"], "crash", fi["discrepancy_id"], "")
            else:
                diags = x["mypy"] or x["ty"] or x["pyright"]
                msg = (diags[0].get("revealed_type") or diags[0]["message"])[:60] if diags else ""
                key = (r["case_id"], x["kind"], x["anchor"], msg + "|" + str(sorted(y.get("code") or "" for y in diags)))
            out.setdefault(key, []).append((fi["tier"], fi["decided_by"], fi.get("dismissal"), o))
    return out


A, B = load(a_dir), load(b_dir)
trans = Counter()
progs = defaultdict(set)
for k, va in A.items():
    vb = B.get(k)
    for i, (tier, by, dis, o) in enumerate(va):
        side = "holdout" if o in hold else "tuning"
        if vb is None or i >= len(vb):
            trans[(side, "disappeared", tier, by)] += 1
            continue
        tier2, by2, dis2, _ = vb[i]
        was = "dismissed" if tier == "dismissed" else "live"
        now = "dismissed" if tier2 == "dismissed" else "live"
        if was != now or by != by2:
            trans[(side, f"{was}->{now}", by, by2)] += 1
            progs[(side, f"{was}->{now}", by, by2)].add(o)
new_keys = [k for k in B if k not in A]
print("findings only in B:", sum(len(B[k]) for k in new_keys))
for k, n in sorted(trans.items(), key=lambda kv: (kv[0][0], -kv[1])):
    print(n, k, "programs=", len(progs.get(k, ())))
