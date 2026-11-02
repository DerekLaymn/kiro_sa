#!/usr/bin/env bash
export TYPEDIFF_LLM=null
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R || exit 1
PY=$R/.venv/bin/python
OUT=campaign/s3-r2-samples3.txt
: > $OUT
echo "######## ty_more_precise" >> $OUT
$PY scripts/kbloop_sample.py runs/day2/out1 reveal_mismatch ty_more_precise --n 12 --ctx 3 >> $OUT 2>&1
