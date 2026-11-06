#!/bin/bash
# usage: run_repros.sh name1 name2 ...  (names of repro/<name>.py; output results/<name>.txt)
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
P=$K/campaign/day10/phase6
for n in "$@"; do
  bash $P/scripts/runall.sh $P/repro/$n.py > $P/results/$n.txt 2>&1
  echo "$n done"
done
