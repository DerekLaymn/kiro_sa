"""Round 2: live findings whose statement depends on a name that is never bound anywhere in the program (the harvester
cut the mdtest/test-suite block that defines it). Direct = statement loads such a name; tainted = loads a name assigned
from an expression that (transitively) loads one."""
import ast
import builtins
import json
import sys
from collections import Counter
from pathlib import Path

run, split, which = sys.argv[1], sys.argv[2], sys.argv[3]
hold = {x for x in Path(split, "holdout.txt").read_text().split("\n") if x}
BUILT = set(dir(builtins)) | {"reveal_type", "assert_type", "__file__", "__name__", "__doc__", "__qualname__", "__module__",
                              "__class__", "__dict__", "__slots__", "__annotations__", "__builtins__", "__spec__",
                              "__loader__", "__package__", "__path__"}


def bound_names(tree):
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            out.add(n.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(n.name)
            if not isinstance(n, ast.ClassDef):
                a = n.args
                out |= {p.arg for p in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg] if p is not None}
            # PEP 695 type params
            for tp in getattr(n, "type_params", []) or []:
                out.add(tp.name)
        elif isinstance(n, ast.Lambda):
            a = n.args
            out |= {p.arg for p in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg] if p is not None}
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                out.add((a.asname or a.name).split(".")[0])
        elif isinstance(n, ast.ExceptHandler) and n.name:
            out.add(n.name)
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            out |= set(n.names)
        elif isinstance(n, (ast.MatchAs, ast.MatchStar)) and getattr(n, "name", None):
            out.add(n.name)
        elif isinstance(n, ast.TypeAlias):
            out.add(n.name.id)
        elif isinstance(n, ast.arg):
            out.add(n.arg)
    return out


cnt = Counter()
ex = {}
progs = Counter()
for f in sorted(Path(run).glob("seed-*.json")):
    r = json.loads(f.read_text())
    o = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    if (which == "tuning") == (o in hold):
        continue
    try:
        tree = ast.parse(r["source"])
    except SyntaxError:
        continue
    b = bound_names(tree)
    loads = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    undef = loads - b - BUILT
    if not undef:
        continue
    # taint propagation over assignments (names, any scope; coarse)
    tainted = set(undef)
    changed = True
    assigns = [n for n in ast.walk(tree) if isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and getattr(n, "value", None) is not None]
    while changed:
        changed = False
        for a in assigns:
            rhs = {x.id for x in ast.walk(a.value) if isinstance(x, ast.Name)}
            if rhs & tainted:
                tg = a.targets if isinstance(a, ast.Assign) else [a.target]
                for t in tg:
                    for x in ast.walk(t):
                        if isinstance(x, ast.Name) and x.id not in tainted:
                            tainted.add(x.id)
                            changed = True
    lines = r["source"].split("\n")
    ds = {d["id"]: d for d in r["discrepancies"]}
    rt = r["runtime"]
    for x in r["findings"]:
        d = ds.get(x["discrepancy_id"])
        if x["tier"] == "dismissed" or d is None:
            continue
        stmt = "\n".join(lines[d["anchor"] - 1:d["anchor_end"]])
        try:
            st = ast.parse(stmt if not stmt.startswith((" ", "\t")) else "if 1:\n" + stmt)
        except SyntaxError:
            st = None
        used = {n.id for n in ast.walk(st) if isinstance(n, ast.Name)} if st else set()
        kind = "direct" if used & undef else "tainted" if used & tainted else None
        if not kind:
            continue
        raised = rt["status"] == "exception" and any(ln == d["anchor"] for ln, _ in rt["frames"])
        key = (kind, d["kind"], "raised" if raised else "no-raise")
        cnt[key] += 1
        progs[Path(o).name] += 1
        ex.setdefault(key, f"{Path(o).name}:L{d['anchor']} undef={sorted(undef)[:3]}")
print("findings", sum(cnt.values()), "programs", len(progs))
for k, n in sorted(cnt.items(), key=lambda kv: -kv[1])[:30]:
    print(n, k, ex[k])
