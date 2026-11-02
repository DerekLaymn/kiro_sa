#!/usr/bin/env bash
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
PY=$R/.venv/bin/python
for rel in uncomparable different gradual; do
  $PY $R/campaign/tmp/dump_reveals.py $R/runs/day2/out0 $R/runs/day2/split $rel 500 > $R/campaign/tmp/reveals-$rel.txt 2>&1
done
