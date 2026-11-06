#!/bin/bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
R=campaign/day10/phase7/results
timeout 60 .venv/bin/python campaign/day10/phase7/gv_rows.py runs/day10/out > $R/gv_rows.out 2>&1
echo "rc=$?" >> $R/gv_rows.out
grep -c "rsv_generics_variance_3c28536f" campaign/day10-triage.txt >> $R/gv_rows.out 2>&1
