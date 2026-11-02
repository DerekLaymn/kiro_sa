import json
import sys
from pathlib import Path

run = sys.argv[1]
for f in sorted(Path(run).glob("seed-*.json")):
    r = json.loads(f.read_text())
    ds = {d["id"]: d for d in r["discrepancies"]}
    rt = r["runtime"]
    for fi in r["findings"]:
        if fi["decided_by"].startswith("kb:") and fi["decided_by"][3:] in ("REVEAL-ERROR-RECOVERY", "MYPY-13807-ALIASED-CONDITIONS", "ASSERT-TYPE-LITERAL-RETENTION"):
            d = ds[fi["discrepancy_id"]]
            if rt["status"] == "exception" and any(ln == d["anchor"] for ln, _ in rt["frames"]):
                print(fi["decided_by"], f.name, "L", d["anchor"], rt["exc_type"], rt["exc_message"][:100], rt["frames"])
                print("  ev:", [(e["strength"], e["supports"], e["summary"][:120]) for e in fi["evidence"]])
                print("  src:", r["source"].split("\n")[d["anchor"] - 1])
