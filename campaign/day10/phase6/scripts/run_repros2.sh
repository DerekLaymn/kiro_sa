#!/bin/bash
# usage: [SRC=repro2 OUT=results2] run_repros2.sh name1 name2 ...  ($SRC/<name>.py -> $OUT/<name>.txt), same checkers as runall.sh
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
P=$K/campaign/day10/phase6
SRC=${SRC:-repro2}
OUT=${OUT:-results2}
mkdir -p $P/$OUT
for n in "$@"; do
  bash $P/scripts/runall.sh $P/$SRC/$n.py > $P/$OUT/$n.txt 2>&1
  echo "$n done"
done
echo finished
