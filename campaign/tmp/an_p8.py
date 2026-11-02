"""Classify the only_ty unresolved-reference live findings (tuning set) by cause. Read-only analysis of saved reports."""
import ast
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

run, split = sys.argv[1], sys.argv[2]
hold = {x for x in Path(split, "holdout.txt").read_text().split("\n") if x}
UNDEF = re.compile(r"Name `(\w+)` used when not defined")
cnt = Counter()
ex = defaultdict(list)
for f in sorted(Path(run).glob("seed-*.json")):
    r = json.loads(f.read_text())
    o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    if o in hold:
        continue
    ds = {d["id"]: d for d in r["discrepancies"]}
    try:
        tree = ast.parse(r["source"])
    except SyntaxError:
        tree = None
    hdr = re.search(r"^#\s*origin:\s*(\S+)", r["source"], re.M)
    origin = hdr.group(1) if hdr else "?"
    for x in r["findings"]:
        d = ds.get(x["discrepancy_id"])
        if x["tier"] == "dismissed" or d is None or d["kind"] != "only_ty":
            continue
        if sorted({y.get("code") or "" for y in d["ty"]}) != ["unresolved-reference"]:
            continue
        names = {m.group(1) for y in d["ty"] if (m := UNDEF.search(y["message"]))}
        mypy_all = [y for y in r.get("diags", {}).get("mypy", [])] if isinstance(r.get("diags"), dict) else []
        # classify each name: module-level class/def/assign defined LATER, or never bound at all, or bound only nested
        kinds = set()
        for nm in names:
            top_later = False
            bound_anywhere = False
            for n in ast.walk(tree) if tree else []:
                if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == nm:
                    bound_anywhere = True
                    if n in tree.body and n.lineno > d["anchor"]:
                        top_later = True
                elif isinstance(n, ast.Name) and n.id == nm and isinstance(n.ctx, (ast.Store, ast.Del)):
                    bound_anywhere = True
                elif isinstance(n, (ast.Import, ast.ImportFrom)) and any((a.asname or a.name).split(".")[0] == nm for a in n.names):
                    bound_anywhere = True
            if top_later:
                kinds.add("defined-later-at-module-level")
            elif bound_anywhere:
                kinds.add("bound-elsewhere(flow)")
            else:
                kinds.add("never-bound")
        rt = r["runtime"]
        key = (origin.split("/")[0], "+".join(sorted(kinds)) or "?", rt["status"] + ":" + str(rt.get("exc_type")))
        cnt[key] += 1
        if len(ex[key]) < 3:
            ex[key].append(f"{Path(o).name} L{d['anchor']}")
tot = sum(cnt.values())
print("total", tot)
for k, n in cnt.most_common():
    print(n, k, ex[k])
