"""Count the dry-run prompts (/tmp/d10-dryrun/inbox) by group, operator and area, and check the 250 budget.
usage: budget.py  -> stdout. Every number in campaign/day10-morning.md section 3 is read from this output.
* operator of a prompt: its `Mutations to apply ...` line (bare name; the two Day-9 operators carry an instruction text);
  fresh programs have an empty list.
* group of a prompt: the file of runs/day10/parents/<GROUP>/ whose text is the `Previous program` of the prompt
  (fresh programs have none -> `fresh`).
* area: the `Feature area:` line, which is the area the generator sees."""
import ast
import collections
import glob
import os
import re

R = "/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/"
parent_text = {}
for p in glob.glob(R + "runs/day10/parents/*/*.py"):
    parent_text[open(p).read().strip()] = os.path.basename(os.path.dirname(p)) + "/" + os.path.basename(p)

LOW_USE = {"gradual_injection", "union_widen", "literal_injection", "inheritance_diamond", "scope_relocation",
           "generic_nesting", "decorator_wrapping", "descriptor_property"}
DAY9_NEW = {"dunder_instance_shadow", "exit_swallow_flip"}
EXHAUSTED = {"match_statement", "recursive_aliases", "dataclasses", "tuples_unpacking", "enums_literals",
             "async_generators", "descriptors_properties"}
NEWEST = {"context_managers", "dunder_dispatch"}
THIN = {"final_classvar", "abstract_classes", "typeddict", "gradual_any", "paramspec_concatenate"}

ops, areas, groups, grp_op, parents = (collections.Counter() for _ in range(5))
fresh_areas = collections.Counter()
instr = unmatched = 0
files = sorted(glob.glob("/tmp/d10-dryrun/inbox/*.prompt.md"))
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
    prev = re.search(r"Previous program \(may be empty\):\n```python\n(.*?)\n```", t, re.S)
    ptxt = prev.group(1).strip() if prev else ""
    if ptxt:
        who = parent_text.get(ptxt)
        if who is None:
            unmatched += 1
            who = "?/?"
        g, pf = who.split("/", 1)
    else:
        g, pf = "fresh", "-"
    area = a.group(1) if a else "?"
    if g == "fresh":
        fresh_areas[area] += 1
    ops[op] += 1
    areas[area] += 1
    groups[g] += 1
    grp_op[(g, op)] += 1
    parents[(g, pf)] += 1
n = len(files)
print("prompts:", n, " distinct files:", len(set(files)), " prompts with a previous program not found among the parents:", unmatched)
print("by group:")
for k, v in sorted(groups.items(), key=lambda kv: (-kv[1], kv[0])):
    print("  %-18s %3d" % (k, v))
print("by group and operator:")
for (g, o), v in sorted(grp_op.items(), key=lambda kv: (kv[0][0], -kv[1], kv[0][1])):
    print("  %-18s %-26s %3d" % (g, o, v))
print("by operator:")
for k, v in sorted(ops.items(), key=lambda kv: (-kv[1], kv[0])):
    print("  %-26s %3d" % (k, v))
print("prompts carrying an operator instruction (Day-9 operators):", instr)
fresh = ops["(fresh)"]
low = sum(v for k, v in ops.items() if k in LOW_USE)
d9 = sum(v for k, v in ops.items() if k in DAY9_NEW)
other = n - fresh - low - d9
print("shares: fresh %d, least-used operators %d, Day-9 instruction operators %d, other operators %d (overload_reorder)" %
      (fresh, low, d9, other))
print("operator prompts: %d; of them with a least-used or Day-9 instruction operator: %d" % (n - fresh, low + d9))
print("by area (as the generator sees it):")
for k, v in sorted(areas.items(), key=lambda kv: (-kv[1], kv[0])):
    tag = "newest" if k in NEWEST else "thin" if k in THIN else "EXHAUSTED" if k in EXHAUSTED else ""
    print("  %-26s %3d  %s" % (k, v, tag))
print("area shares: newest areas %d, thin areas %d, exhausted families %d, other %d" % (
    sum(areas[k] for k in NEWEST), sum(areas[k] for k in THIN), sum(areas[k] for k in EXHAUSTED),
    n - sum(areas[k] for k in NEWEST | THIN | EXHAUSTED)))
print("fresh programs by area:")
for k, v in sorted(fresh_areas.items(), key=lambda kv: (-kv[1], kv[0])):
    print("  %-26s %3d" % (k, v))
print("fresh in the newest areas: %d; fresh in the other areas: %d" % (
    sum(fresh_areas[k] for k in NEWEST), sum(fresh_areas.values()) - sum(fresh_areas[k] for k in NEWEST)))
print("programs per parent:")
for (g, pf), v in sorted(parents.items()):
    print("  %-18s %-80s %3d" % (g, pf[:80], v))
