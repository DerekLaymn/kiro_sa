#!/bin/bash
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd /tmp/d7/w
for f in c2min r6 r8 r4; do
  $K/.venv/bin/pyright --pythonversion 3.13 $f.py > /tmp/d7pd/pr_$f.txt 2>&1
  echo "$f pyright 1.1.414 exit=$? first-line: $(head -1 /tmp/d7pd/pr_$f.txt | cut -c1-120)"
done
echo "--- node version / stack size"
ls $K/.venv/lib/python3.13/site-packages/pyright 2>&1 | head -3
