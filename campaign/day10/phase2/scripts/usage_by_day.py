"""Day 10 morning: how often each mutation operator and each feature area was used on Days 3 to 9, read from the
file-bridge prompts (runs/dayN/inbox/*.prompt.md: `Feature area:` line and `Mutations to apply ...` line).
usage: usage_by_day.py  -> stdout (tables: operators x days, areas x days, all 24 areas and all 23 operators listed)."""
import ast
import collections
import glob
import re
import sys

R = "/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/"
sys.path.insert(0, R)
from typediff.strategy import AREAS  # noqa: E402
from typediff.operators import OPERATORS as NEW_OPS  # noqa: E402

DAYS = range(3, 10)
ALL_OPS = ["variance_flip", "bound_constraint_swap", "generic_nesting", "union_widen", "literal_injection",
           "gradual_injection", "narrowing_construct_swap", "annotation_spelling_swap", "scope_relocation",
           "protocol_vs_abc", "qualifier_toggle", "overload_reorder", "recursion_deepening", "invalid_type_form",
           "python_version_flip", "feature_crossover", "runtime_witness", "inheritance_diamond", "descriptor_property",
           "decorator_wrapping", "async_generator_wrap", "dunder_instance_shadow", "exit_swallow_flip"]
ops = {d: collections.Counter() for d in DAYS}
areas = {d: collections.Counter() for d in DAYS}
for d in DAYS:
    for f in glob.glob(R + "runs/day%d/inbox/*.prompt.md" % d):
        t = open(f).read()
        a = re.search(r"^Feature area:\s*(\S+)", t, re.M)
        m = re.search(r"^Mutations to apply to the previous program \(if any\): (.*)$", t, re.M)
        try:
            muts = ast.literal_eval(m.group(1)) if m else []
        except (ValueError, SyntaxError):
            muts = []
        if not isinstance(muts, list):
            muts = []
        for x in muts:
            ops[d][x["operator"]] += 1
        areas[d][a.group(1) if a else "?"] += 1
print("prompts per day:", {d: sum(areas[d].values()) for d in DAYS})
print()
print("operator uses per day (Days 3..9), total, number of days used")
print("%-26s" % "operator" + "".join("%5s" % ("d%d" % d) for d in DAYS) + "%7s%6s" % ("total", "days"))
for o in sorted(ALL_OPS, key=lambda o: (sum(ops[d][o] for d in DAYS), o)):
    row = [ops[d][o] for d in DAYS]
    print("%-26s" % o + "".join("%5d" % n for n in row) + "%7d%6d" % (sum(row), sum(1 for n in row if n)))
extra = {o for d in DAYS for o in ops[d]} - set(ALL_OPS)
print("operators in the prompts that are not in the strategist list:", sorted(extra))
print()
print("area prompts per day (Days 3..9), total, last day with a prompt")
print("%-26s" % "area" + "".join("%5s" % ("d%d" % d) for d in DAYS) + "%7s%6s" % ("total", "last"))
for a in sorted(AREAS, key=lambda a: (sum(areas[d][a] for d in DAYS), a)):
    row = [areas[d][a] for d in DAYS]
    last = max((d for d in DAYS if areas[d][a]), default=0)
    print("%-26s" % a + "".join("%5d" % n for n in row) + "%7d%6s" % (sum(row), last or "-"))
print("new-operator names with their own instruction text:", sorted(NEW_OPS))
