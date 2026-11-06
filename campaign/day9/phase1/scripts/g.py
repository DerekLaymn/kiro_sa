import json, sys
r = json.load(open(sys.argv[1]))
for d in r["discrepancies"]:
    print(d["id"], d["kind"], d.get("anchor"), [x["message"] for x in d["mypy"]], [x["message"] for x in d["ty"]])
for x in r["findings"]:
    print(x["discrepancy_id"], x["tier"], x.get("dismissal"), x.get("kb_id") or x.get("entry"), x["reasoning"][:200])
