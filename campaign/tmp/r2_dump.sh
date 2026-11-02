#!/usr/bin/env bash
export TYPEDIFF_LLM=null
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R || exit 1
PY=$R/.venv/bin/python
for rel in gradual different uncomparable ty_more_precise mypy_more_precise; do
  $PY campaign/tmp/dump_reveals.py runs/day2/out1 docs/kb-loop-split $rel 60 > campaign/s3-r2-reveals-$rel.txt 2>&1
done
