"""Numbers quoted in campaign/day3-morning.md that need an exact count."""
import json
from pathlib import Path

RUN = Path("/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/runs/day3/replay")
strong = nameerr = subscript = 0
crash_rows = []
for f in sorted(RUN.glob("seed-*.json")):
    r = json.loads(f.read_text())
    ds = {d["id"]: d for d in r["discrepancies"]}
    origin = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    for x in r["findings"]:
        if x["tier"] == "dismissed" or x.get("dismissal"):
            continue
        ev = [e for e in x.get("evidence") or [] if e.get("strength") == "strong" and e.get("supports") == "bug"]
        if not ev:
            continue
        strong += 1
        txt = " ".join(e["summary"] for e in ev)
        if "NameError" in txt or "UnboundLocalError" in txt:
            nameerr += 1
        if "is not subscriptable" in txt:
            subscript += 1
        if x["discrepancy_id"].startswith("C"):
            crash_rows.append((f.stem, origin.split("/")[-1], x.get("faulty_tool"), x.get("signature"), [c["signature"][:60] for c in r["crashes"]]))
print("live strong:", strong, "NameError/UnboundLocalError in strong evidence:", nameerr, "'not subscriptable':", subscript)
for row in crash_rows:
    print(row)
