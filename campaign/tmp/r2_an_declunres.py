"""Round 2: live only_mypy findings (all codes) whose used names are declared with an annotation containing a name that
ty itself flagged unresolved-reference at the declaration line (ty's declared type is then Unknown)."""
import ast
import json
import re
import sys
from collections import Counter
from pathlib import Path

run, split, which = sys.argv[1], sys.argv[2], sys.argv[3]
hold = {x for x in Path(split, "holdout.txt").read_text().split("\n") if x}
UNDEF = re.compile(r"Name `(\w+)` used when not defined")
cnt = Counter()
ex = {}
total = Counter()
for f in sorted(Path(run).glob("seed-*.json")):
    r = json.loads(f.read_text())
    o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    if (which == "tuning") == (o in hold):
        continue
    try:
        tree = ast.parse(r["source"])
    except SyntaxError:
        continue
    ty_unres = {}
    for y in r["diagnostics"]["ty"]:
        m = UNDEF.search(y["message"])
        if m and y.get("code") == "unresolved-reference":
            ty_unres.setdefault(y["line"], set()).add(m.group(1))
    # declared names -> set of unresolved names in annotation at the declaration line
    decl = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            names = {x.id for x in ast.walk(n.annotation) if isinstance(x, ast.Name)}
            bad = names & ty_unres.get(n.lineno, set())
            if bad:
                decl.setdefault(n.target.id, set()).update(bad)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = n.args
            for p in [*a.posonlyargs, *a.args, *a.kwonlyargs]:
                if p.annotation is not None:
                    names = {x.id for x in ast.walk(p.annotation) if isinstance(x, ast.Name)}
                    bad = names & ty_unres.get(n.lineno, set())
                    if bad:
                        decl.setdefault(p.arg, set()).update(bad)
    lines = r["source"].split("\n")
    ds = {d["id"]: d for d in r["discrepancies"]}
    rt = r["runtime"]
    for x in r["findings"]:
        d = ds.get(x["discrepancy_id"])
        if x["tier"] == "dismissed" or d is None or d["kind"] != "only_mypy":
            continue
        stmt = "\n".join(lines[d["anchor"] - 1:d["anchor_end"]])
        try:
            st = ast.parse(stmt.strip() if not stmt.startswith((" ", "\t")) else "if 1:\n" + stmt)
        except SyntaxError:
            st = None
        used = {n.id for n in ast.walk(st) if isinstance(n, ast.Name)} if st else set()
        raised = rt["status"] == "exception" and any(ln == d["anchor"] for ln, _ in rt["frames"])
        total[(tuple(sorted({y.get("code") or "" for y in d["mypy"]})))] += 1
        if used & set(decl):
            key = (",".join(sorted({y.get("code") or "" for y in d["mypy"]})), "raised" if raised else "no-raise")
            cnt[key] += 1
            ex.setdefault(key, f"{Path(o).name}:L{d['anchor']} {sorted(used & set(decl))}")
print("hits", sum(cnt.values()), "of only_mypy live", sum(total.values()))
for k, n in sorted(cnt.items(), key=lambda kv: -kv[1])[:30]:
    print(n, k, ex[k])
