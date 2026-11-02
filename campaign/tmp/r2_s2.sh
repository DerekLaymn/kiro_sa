#!/usr/bin/env bash
export TYPEDIFF_LLM=null
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R || exit 1
PY=$R/.venv/bin/python
OUT=campaign/s3-r2-samples2.txt
: > $OUT
s() { echo "######## $1 $2" >> $OUT; $PY scripts/kbloop_sample.py runs/day2/out1 "$@" --ctx 1 >> $OUT 2>&1; }
s only_mypy assignment --n 10
s only_mypy assert-type --n 8
s only_ty unresolved-reference --n 8
s only_mypy arg-type --n 6
s only_ty type-assertion-failure --n 8
s only_ty invalid-assignment --n 6
