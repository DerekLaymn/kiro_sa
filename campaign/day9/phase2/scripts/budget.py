"""Count the dry-run prompts (/tmp/d9-dryrun/inbox) by operator and by area, and check the 250 budget.
usage: budget.py  -> stdout. The operator of a prompt is read from its `Mutations to apply ...` line (bare name, or the
Day-9 operators with their instruction text); fresh programs have an empty list."""
import ast
import collections
import glob
import re

ops, areas, both = collections.Counter(), collections.Counter(), collections.Counter()
instr = 0
files = sorted(glob.glob("/tmp/d9-dryrun/inbox/*.prompt.md"))
for f in files:
    t = open(f).read()
    a = re.search(r"^Feature area:\s*(\S+)", t, re.M)
    m = re.search(r"^Mutations to apply to the previous program \(if any\): (.*)$", t, re.M)
    try:
        muts = ast.literal_eval(m.group(1)) if m else []
    except (ValueError, SyntaxError):  # fresh programs print a word such as `none` instead of a list
        muts = []
    if not isinstance(muts, list):
        muts = []
    op = muts[0]["operator"] if muts else "(fresh)"
    if muts and "instruction" in muts[0]:
        instr += 1
    ops[op] += 1
    areas[a.group(1) if a else "?"] += 1
    both[(op, a.group(1) if a else "?")] += 1
print("prompts:", len(files))
print("by operator:")
for k, v in sorted(ops.items(), key=lambda kv: (-kv[1], kv[0])):
    print("  %-26s %3d" % (k, v))
print("prompts carrying an operator instruction (Day-9 operators):", instr)
print("by area:")
for k, v in sorted(areas.items(), key=lambda kv: (-kv[1], kv[0])):
    print("  %-26s %3d" % (k, v))
