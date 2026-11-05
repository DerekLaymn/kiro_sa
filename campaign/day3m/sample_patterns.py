"""For the biggest live patterns of the replay: origin-source mix, strong-evidence share, and 5 seeded random non-strong examples."""
import collections
import json
import random
from pathlib import Path

RUN = Path("/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/runs/day3/replay")
PATTERNS = {
    "reveal|uncomparable": lambda d, c: d["kind"] == "reveal_mismatch" and d.get("reveal_relation") == "uncomparable",
    "reveal|different": lambda d, c: d["kind"] == "reveal_mismatch" and d.get("reveal_relation") == "different",
    "reveal|ty_more_precise": lambda d, c: d["kind"] == "reveal_mismatch" and d.get("reveal_relation") == "ty_more_precise",
    "reveal|gradual": lambda d, c: d["kind"] == "reveal_mismatch" and d.get("reveal_relation") == "gradual",
    "reveal|mypy_more_precise": lambda d, c: d["kind"] == "reveal_mismatch" and d.get("reveal_relation") == "mypy_more_precise",
    "only_mypy|assert-type": lambda d, c: d["kind"] == "only_mypy" and "assert-type" in c["mypy"],
    "only_mypy|arg-type": lambda d, c: d["kind"] == "only_mypy" and "arg-type" in c["mypy"],
    "concern|assignment": lambda d, c: d["kind"] == "concern_mismatch" and "assignment" in c["mypy"],
}
rng = random.Random(11)
groups = collections.defaultdict(list)
for f in sorted(RUN.glob("seed-*.json")):
    r = json.loads(f.read_text())
    ds = {d["id"]: d for d in r["discrepancies"]}
    origin = next((n.split("=", 1)[1].removeprefix("seed ") for n in r["notes"] if n.startswith("origin=")), "")
    src = "mypy-suite" if "mypy__" in origin else "ty-mdtest" if "/ty__" in origin else "pyright" if "pyright__" in origin else "conformance" if "conformance__" in origin else "typeshed" if "typeshed__" in origin else "other"
    for x in r["findings"]:
        if x["tier"] == "dismissed" or x.get("dismissal"):
            continue
        d = ds.get(x["discrepancy_id"])
        if not d:
            continue
        c = {"mypy": {m.get("code") for m in d.get("mypy") or []}, "ty": {m.get("code") for m in d.get("ty") or []}}
        strong = any(e.get("strength") == "strong" and e.get("supports") == "bug" for e in x.get("evidence") or [])
        for name, pred in PATTERNS.items():
            if pred(d, c):
                groups[name].append((src, strong, f.stem, d, x, r))
for name, rows in groups.items():
    print("=" * 100)
    print(name, len(rows), "findings; strong:", sum(1 for r in rows if r[1]), "; sources:", dict(collections.Counter(r[0] for r in rows)))
    hints = collections.Counter(h for r in rows for h in (r[3].get("kb_hits") or []))
    print("   kb hints:", dict(hints.most_common(6)))
    non = [r for r in rows if not r[1]]
    for src, strong, stem, d, x, rep in rng.sample(non, min(5, len(non))):
        def first(lst):
            return (str(lst[0].get("revealed_type") or lst[0].get("message")) if lst else "-")[:90]
        print(f"  [{src}] {stem} {d['id']} L{d['anchor']} {d['statement'][:70]!r}\n      mypy={first(d.get('mypy'))}  ty={first(d.get('ty'))}")
