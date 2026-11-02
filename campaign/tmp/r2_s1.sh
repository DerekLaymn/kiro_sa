#!/usr/bin/env bash
export TYPEDIFF_LLM=null
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R || exit 1
PY=$R/.venv/bin/python
OUT=campaign/s3-r2-samples1.txt
: > $OUT
echo "######## gradual" >> $OUT
$PY scripts/kbloop_sample.py runs/day2/out1 reveal_mismatch gradual --n 8 --ctx 2 >> $OUT 2>&1
echo "######## different" >> $OUT
$PY scripts/kbloop_sample.py runs/day2/out1 reveal_mismatch different --n 8 --ctx 2 >> $OUT 2>&1
echo "######## uncomparable" >> $OUT
$PY scripts/kbloop_sample.py runs/day2/out1 reveal_mismatch uncomparable --n 8 --ctx 2 >> $OUT 2>&1
