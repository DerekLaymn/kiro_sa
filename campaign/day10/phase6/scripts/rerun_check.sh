#!/bin/bash
# re-run all 30 programs of the interrupted run (10 verbatim p_*, 20 reductions c_*) and compare the one-line summaries with the saved results
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
P=$K/campaign/day10/phase6
cd $P || exit 1
names=$(ls repro | sed 's/\.py$//')
SRC=repro OUT=results_rerun bash scripts/run_repros2.sh $names > rerun.log 2>&1
$K/.venv/bin/python - <<'EOF' > results_rerun/compare.out 2>&1
import os, re, subprocess, sys
P = "/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day10/phase6"
names = sorted(f[:-3] for f in os.listdir(P + "/repro"))
def summ(d, n):
    env = dict(os.environ, RESDIR=d)
    # summarize.py writes <d>/<n>.sum.txt
    subprocess.run([sys.executable, P + "/scripts/summarize.py", n], env=env, check=True, stdout=subprocess.DEVNULL)
    t = open(f"{P}/{d}/{n}.sum.txt").read()
    # drop timing-dependent / path-dependent lines
    t = re.sub(r"0x[0-9a-f]+", "0xADDR", t)
    t = t.replace("repro/", "")
    return t
same = diff = 0
for n in names:
    a = summ("results", n)
    b = summ("results_rerun", n)
    if a == b:
        same += 1
    else:
        diff += 1
        print("DIFF", n)
        import difflib
        for ln in difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=0):
            print("   ", ln)
print("programs", len(names), "identical", same, "different", diff)
EOF
echo finished >> rerun.log
