"""Round 3: live reveal rows where ONE tool reveals exactly Unknown (ty) / Any (mypy) and the other a non-gradual type.
Why is the tool gradual? own binding flagged earlier (flagged_bindings), undefined/unresolved-import names, nothing.
usage: r3_an_gradual.py RUN"""
import ast
import json
import sys
from collections import Counter
from pathlib import Path

from typediff.kb import _reveal_arg_call
from typediff.models import Tool
from typediff.replay import state_from_report
from typediff.rules import flagged_bindings
from typediff.typenorm import normalize

run = Path(sys.argv[1])
hold = {x for x in Path("runs/day2/split/holdout.txt").read_text().split("\n") if x}
cnt = Counter()
ex = {}
for f in sorted(run.glob("seed-*.json")):
    r = json.loads(f.read_text())
    o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    sp = "holdout" if o in hold else "tuning"
    ds = {d["id"]: d for d in r["discrepancies"]}
    st = None
    for x in r["findings"]:
        d = ds.get(x["discrepancy_id"])
        if x["tier"] == "dismissed" or d is None or d["kind"] != "reveal_mismatch" or len(d["ty"]) != 1 or len(d["mypy"]) != 1:
            continue
        ty, my = d["ty"][0].get("revealed_type") or "", d["mypy"][0].get("revealed_type") or ""
        side = "ty" if ty.strip() == "Unknown" else "mypy" if my.strip() == "Any" else None
        if side is None:
            continue
        other = my if side == "ty" else ty
        n = normalize(other, None)
        if n.node is None or "gradual" in n.flags or "todo" in n.flags:
            continue
        st = st or state_from_report(r)
        rt = r["runtime"]
        raised = rt["status"] == "exception" and any(ln == d["anchor"] for ln, _ in rt["frames"])
        diag = next(y for y in st.diags[Tool(side)] if y.revealed_type is not None and y.line == d[side][0]["line"] and y.col == d[side][0]["col"])
        call = _reveal_arg_call(st, diag)
        names = {a.id for a in ast.walk(call.args[0]) if isinstance(a, ast.Name)} if call is not None else set()
        fb = flagged_bindings(st, Tool(side), names, d["anchor"]) if names else []
        first_err = [y for y in st.diags[Tool(side)] if y.is_problem and y.revealed_type is None and st.amap.anchor(y.line) < d["anchor"]]
        key = (sp, side, "raised" if raised else "no-raise",
               "flagged-binding" if fb else ("no-names" if not names else ("earlier-error" if first_err else "clean")))
        cnt[key] += 1
        ex.setdefault(key, []).append(f"{Path(o).name}:L{d['anchor']} {side}={'Unknown' if side == 'ty' else 'Any'} other={other[:30]} fb={fb[:2]}")
for k, v in sorted(cnt.items()):
    print(v, k)
print()
for k, lst in sorted(ex.items()):
    print(k)
    for s in lst[:5]:
        print("    ", s)
