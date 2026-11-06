"""Print the three reveals of the two Day-7 rows that left DISPLAY-EQUIVALENT in iteration 2."""
import json
import sys
from pathlib import Path

for rid in ("seed-a241555c6e22", "seed-d1dc5d208df4"):
    for p in Path("runs/day8/day7replay-it2").rglob("*.json"):
        if rid in p.name:
            r = json.loads(p.read_text())
            for f in r.get("findings", []):
                d = f.get("discrepancy", f)
                if "Child.__init__" in json.dumps(d)[:2000]:
                    print(rid, p.name)
                    for k in ("mypy", "ty", "pyright"):
                        for x in d.get(k, []):
                            print("  ", k, x.get("revealed_type") or x.get("message"))
                    break
            break
