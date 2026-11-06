#!/bin/bash
# usage: sum2.sh outfile name...   summarises results2/<name>.txt (ty/mypy/pyright/cpython one line per diagnostic)
P=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/campaign/day10/phase6
out="$1"; shift
RESDIR=results2 /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin/python $P/scripts/summarize.py "$@" > /dev/null
: > "$out"
for n in "$@"; do
  echo "######## $n" >> "$out"
  cat $P/results2/$n.sum.txt >> "$out"
done
