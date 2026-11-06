import glob, json, os, sys
R = "/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/"
want = sys.argv[1:]
for f in sorted(glob.glob(R + "runs/day9/day8replay/seed-*.json")):
    d = json.load(open(f))
    origin = next((x[7:] for x in d["notes"] if x.startswith("origin=")), "")
    base = os.path.basename(origin.replace("seed ", ""))
    if not any(w in base for w in want):
        continue
    print("=====", base)
    ds = {x["id"]: x for x in d["discrepancies"]}
    for fi in d["findings"]:
        if fi["tier"] == "dismissed":
            continue
        x = ds.get(fi["discrepancy_id"])
        if not x:
            print("  crash", fi.get("signature"))
            continue
        def sh(l):
            return "; ".join((y.get("revealed_type") and "reveal " + str(y["revealed_type"])) or "[%s] %s" % (y.get("code"), y["message"]) for y in l)[:150] or "-"
        print("  %s %s L%s stmt=%r" % (x["id"], x["kind"], x["anchor"], x["statement"][:60]))
        print("     mypy:", sh(x["mypy"]))
        print("     ty:  ", sh(x["ty"]))
        print("     pyr: ", sh(x["pyright"]))
