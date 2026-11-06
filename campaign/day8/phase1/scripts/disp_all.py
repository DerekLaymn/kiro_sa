import json, glob, sys
for run in sys.argv[1:]:
    print("#####", run)
    for f in sorted(glob.glob(run + "/seed-*.json")):
        r = json.load(open(f))
        ds = {d["id"]: d for d in r["discrepancies"]}
        for fi in r["findings"]:
            if fi["decided_by"] == "kb:DISPLAY-EQUIVALENT":
                d = ds[fi["discrepancy_id"]]
                print(f.split("/")[-1], d["id"], d["statement"][:60])
                print("   mypy   :", d["mypy"][0]["revealed_type"])
                print("   ty     :", d["ty"][0]["revealed_type"])
                print("   pyright:", [p["revealed_type"] for p in d["pyright"] if p["revealed_type"]])
