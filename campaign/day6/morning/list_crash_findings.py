"""List every crash finding (live and dismissed) in a run dir with its origin program.
Usage: python list_crash_findings.py runs/day5/out97"""
import json
import sys
from pathlib import Path

run = Path(sys.argv[1])
for f in sorted(run.glob("*.json")):
    try:
        r = json.loads(f.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError):
        continue
    if "findings" not in r:
        continue
    origin = next((n.split("=", 1)[1] for n in r.get("notes", []) if n.startswith("origin=")), r["case_id"])
    for x in r["findings"]:
        if x.get("symptom") != "CRASH":
            continue
        closed = (x.get("closed_by") or "-").split(" ")[0]
        print(f"{x['tier']:9} {x.get('faulty_tool',''):8} {x.get('signature','')[:40]:40} {closed:11} "
              f"{f.stem[5:17]} {Path(origin.removeprefix('seed ')).name}")
