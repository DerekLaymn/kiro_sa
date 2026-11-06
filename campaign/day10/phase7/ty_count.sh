#!/bin/bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
O=campaign/day10/phase7/results/ty_count_gv.out
: > $O
for f in runs/day10/gen/generics_variance/rsv_generics_variance_3c28536f__mut0_*.py; do
  n=$(timeout 60 .venv/bin/ty check --python-version 3.13 --output-format concise "$f" 2>&1 | grep -c -E '(error|warning)\[')
  echo "$f ty_diagnostics=$n" >> $O
done
echo finished >> $O
