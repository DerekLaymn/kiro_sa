#!/bin/bash
# py_compile every promoted parent (as the step requires), then re-run the pipeline on the one file changed after the full hits run (A5).
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R
n=0; bad=0
for f in runs/hits/*.py; do
  n=$((n+1))
  $R/.venv/bin/python -m py_compile "$f" || { bad=$((bad+1)); echo "BAD $f"; }
done
rm -rf runs/hits/__pycache__
echo "py_compile: $n files, $bad failures"
rm -rf runs/day3/a5check; mkdir -p runs/day3/a5check/in
cp runs/hits/d3p_self_classmethods_self_call_union.py runs/day3/a5check/in/
TYPEDIFF_LLM=null $R/.venv/bin/typediff --out $R/runs/day3/a5check/out --python-version 3.13 seeds $R/runs/day3/a5check/in
ls runs/hits | wc -l
