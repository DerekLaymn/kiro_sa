"""Classify only_mypy [assignment] live findings (tuning) by the assignment target shape and whether pyright/ty agree."""
import ast
import json
import re
import sys
from collections import Counter
from pathlib import Path

run, split = sys.argv[1], sys.argv[2]
hold = {x for x in Path(split, "holdout.txt").read_text().split("\n") if x}
cnt = Counter()
ex = {}


def declared_names(tree):
    """names with an annotation anywhere (AnnAssign / parameter annotation)"""
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            out.add(n.target.id)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = n.args
            for p in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg]:
                if p is not None and p.annotation is not None:
                    out.add(p.arg)
    return out


for f in sorted(Path(run).glob("seed-*.json")):
    r = json.loads(f.read_text())
    o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    if o in hold:
        continue
    try:
        tree = ast.parse(r["source"])
    except SyntaxError:
        continue
    decl = declared_names(tree)
    lines = r["source"].split("\n")
    ds = {d["id"]: d for d in r["discrepancies"]}
    for x in r["findings"]:
        d = ds.get(x["discrepancy_id"])
        if x["tier"] == "dismissed" or d is None or d["kind"] != "only_mypy":
            continue
        if sorted({y.get("code") or "" for y in d["mypy"]}) != ["assignment"]:
            continue
        if not all(y["message"].startswith("Incompatible types in assignment (expression has type") and "base class" not in y["message"] for y in d["mypy"]):
            continue
        ln = d["anchor"]
        node = None
        for n in ast.walk(tree):
            if isinstance(n, (ast.Assign, ast.AugAssign, ast.AnnAssign)) and n.lineno <= ln <= (n.end_lineno or n.lineno):
                node = n
                break
        if node is None:
            shape = "other-stmt"
        elif isinstance(node, ast.AnnAssign):
            shape = "annassign"
        else:
            tg = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(tg, ast.Name):
                shape = ("augassign" if isinstance(node, ast.AugAssign) else "assign") + ("-name-declared" if tg.id in decl else "-name-undeclared")
            elif isinstance(tg, ast.Attribute):
                shape = "assign-attr"
            elif isinstance(tg, ast.Subscript):
                shape = "assign-subscript"
            else:
                shape = "assign-tuple/other"
        pyr = [y for y in r["diagnostics"]["pyright"] if d["anchor"] <= y["line"] <= d["anchor_end"] and y["severity"] == "error"]
        rt = r["runtime"]
        raised = rt["status"] == "exception" and any(l == d["anchor"] for l, _ in rt["frames"])
        suite = bool(re.search(r"#\s*E:|#\s*error|should generate", "\n".join(lines[max(0, ln - 2):d["anchor_end"]])))
        key = (shape, "pyright-agrees" if pyr else "pyright-silent", "cpython-raised" if raised else "ok", "suite-expects-err" if suite else "")
        cnt[key] += 1
        ex.setdefault(key, f"{Path(o).name}:L{ln}")
tot = sum(cnt.values())
print("total", tot)
for k, n in sorted(cnt.items(), key=lambda kv: -kv[1])[:30]:
    print(n, k, ex[k])
