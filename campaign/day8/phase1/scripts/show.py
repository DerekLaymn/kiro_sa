"""show.py RUN SEEDSTEM[:D] ... : print program lines around the anchor and the diagnostics of the finding"""
import json, sys
run = sys.argv[1]
for arg in sys.argv[2:]:
    stem, _, did = arg.partition(":")
    r = json.load(open(f"{run}/{stem}.json"))
    src = r["source"].splitlines()
    for d in r["discrepancies"]:
        if did and d["id"] != did:
            continue
        print("=" * 100)
        print(stem, d["id"], d["kind"], "anchor", d["anchor"], d["statement"][:100])
        lo = max(0, d["anchor"] - 8)
        for i in range(lo, min(len(src), d["anchor"] + 2)):
            print(f"{i + 1:4d} {src[i]}")
        for t in ("mypy", "ty", "pyright"):
            for x in d[t][:3]:
                print("   ", t, x["code"], (x["message"] or x["revealed_type"] or "")[:200].replace("\n", " "))
        f = next(f for f in r["findings"] if f["discrepancy_id"] == d["id"])
        print("    ->", f["tier"], f["dismissal"], f["decided_by"])
