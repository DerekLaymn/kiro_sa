"""Day 9 preflight: how many generated programs follow the two new operators (plan day9-morning.md section 10).

Group = the `runs/day9/parents/<GROUP>/` in the first `# origin:` comment line of each generated program.
  exit_swallow_flip      -> program defines `__exit__` or `__aexit__` (D_exit, H_dunder)
  dunder_instance_shadow -> program has an annotation-only dunder in a class body, or a dunder assigned on an
                            instance / outside the class body (D_shadow, H_dunder)
Usage: operator_follow.py [gen_dir]
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

gen = Path(sys.argv[1] if len(sys.argv) > 1 else "runs/day9/gen")
IGNORE = {"__slots__", "__match_args__", "__all__", "__annotations__", "__doc__", "__dict__", "__name__",
          "__class__", "__module__", "__qualname__", "__future__", "__main__", "__version__", "__file__"}
EXIT = re.compile(r"^\s*(?:async\s+)?def\s+__a?exit__\s*\(", re.M)
ANN_ONLY = re.compile(r"^[ \t]+(__\w+__)\s*:\s*[^=\n]+$", re.M)            # `    __call__: Callable[...]`
INST_ASSIGN = re.compile(r"\b(?:self|cls|[a-z_]\w*)\.(__\w+__)\s*=(?!=)", re.M)  # `obj.__call__ = ...`
ORIGIN = re.compile(r"^# origin: runs/day9/parents/(\w+)/", re.M)

rows = defaultdict(lambda: {"n": 0, "exit": 0, "ann": 0, "inst": 0, "shadow": 0})
for p in sorted(gen.rglob("*.py")):
    src = p.read_text()
    m = ORIGIN.search(src)
    if not m:
        continue
    g = m.group(1)
    r = rows[g]
    r["n"] += 1
    r["exit"] += bool(EXIT.search(src))
    ann = [d for d in ANN_ONLY.findall(src) if d not in IGNORE]
    inst = [d for d in INST_ASSIGN.findall(src) if d not in IGNORE]
    r["ann"] += bool(ann)
    r["inst"] += bool(inst)
    r["shadow"] += bool(ann or inst)

print(f"{'group':16} {'n':>3} {'__exit__':>9} {'ann-only':>9} {'inst-assign':>12} {'either shadow':>14}")
for g in sorted(rows):
    r = rows[g]
    print(f"{g:16} {r['n']:>3} {r['exit']:>9} {r['ann']:>9} {r['inst']:>12} {r['shadow']:>14}")
