"""ASSERT-TYPE dismissals where the FAILING tool's type has no Literal but the asserted type has (tool widened)."""
import json
import re
import sys
from pathlib import Path

run = sys.argv[1]
TY = re.compile(r"^Type `(?P<a>.+)` does not match asserted type `(?P<b>.+)`$")
MY = re.compile(r'^Expression is of type "(?P<a>.+)", not "(?P<b>.+)"$')
n = 0
for f in sorted(Path(run).glob("seed-*.json")):
    r = json.loads(f.read_text())
    ds = {d["id"]: d for d in r["discrepancies"]}
    o = next((x.split("=", 1)[1].removeprefix("seed ") for x in r["notes"] if x.startswith("origin=")), "")
    lines = r["source"].split("\n")
    for fi in r["findings"]:
        if fi["decided_by"] != "kb:ASSERT-TYPE-LITERAL-RETENTION":
            continue
        d = ds[fi["discrepancy_id"]]
        x = (d["ty"] or d["mypy"])[0]
        m = (TY if d["ty"] else MY).match(x["message"])
        if not m or "Literal" in m["a"] or "Literal" not in m["b"]:
            continue
        n += 1
        has_decl_literal = [i + 1 for i, l in enumerate(lines) if "Literal[" in l and "assert_type" not in l and not l.lstrip().startswith("#")]
        print(f"--- {Path(o).name} L{d['anchor']} tool={'ty' if d['ty'] else 'mypy'}: {x['message'][:100]}")
        print("   stmt:", lines[d['anchor'] - 1].strip()[:110])
        print("   other lines mentioning Literal[ (not assert_type):", has_decl_literal[:6])
print("total widened-direction dismissals:", n)
