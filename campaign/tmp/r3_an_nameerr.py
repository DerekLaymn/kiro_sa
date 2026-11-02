"""Toggle experiment over the live only_ty [unresolved-reference] rows of a run: does mypy report the name when
`--enable-error-code possibly-undefined --enable-error-code used-before-def` is on?  usage: r3_an_nameerr.py RUN [tuning|holdout|all]"""
import json
import sys
from collections import Counter
from pathlib import Path

from typediff.models import Tool
from typediff.runners import Runners, ToolConfig

FLAGS = ["--enable-error-code", "possibly-undefined", "--enable-error-code", "used-before-def"]
run = Path(sys.argv[1])
which = sys.argv[2] if len(sys.argv) > 2 else "all"
hold = {x for x in Path("runs/day2/split/holdout.txt").read_text().split("\n") if x}
R = Runners(ToolConfig(python_version="3.13"))
tot = Counter()
rows = []
for f in sorted(run.glob("seed-*.json")):
    r = json.loads(f.read_text())
    o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    sp = "holdout" if o in hold else "tuning"
    if which != "all" and sp != which:
        continue
    ds = {d["id"]: d for d in r["discrepancies"]}
    for x in r["findings"]:
        d = ds.get(x["discrepancy_id"])
        if x["tier"] == "dismissed" or d is None or d["kind"] != "only_ty":
            continue
        if not d["ty"] or not all(y.get("code") == "unresolved-reference" for y in d["ty"]) or d["mypy"]:
            continue
        res = R.check(Tool.MYPY, r["source"], FLAGS)
        anchor_lines = set(range(d["anchor"], d["anchor_end"] + 1))
        hit = [y for y in res.diagnostics if y.line in anchor_lines and (y.code in ("possibly-undefined", "used-before-def", "name-defined"))]
        rt = r["runtime"]
        raised = rt["status"] == "exception" and rt.get("exc_type") in ("NameError", "UnboundLocalError")
        key = (sp, "toggle-reports" if hit else "toggle-silent", "nameerror" if raised else "no-nameerror")
        tot[key] += 1
        rows.append((o, d["id"], d["anchor"], key, [y.code for y in hit], [y["message"][:60] for y in d["ty"]][:1]))
for k, v in sorted(tot.items()):
    print(k, v)
print()
for row in rows[:400]:
    print(row)
