#!/usr/bin/env bash
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
PY=$R/.venv/bin/python
for rel in gradual different uncomparable ty_more_precise mypy_more_precise; do
  echo "##### reveal_mismatch $rel"
  $PY $R/campaign/tmp/by_origin.py $R/runs/day2/out0 $R/runs/day2/split reveal_mismatch $rel | head -16
done
for k in only_mypy only_ty concern_mismatch; do
  echo "##### $k"
  $PY $R/campaign/tmp/by_origin.py $R/runs/day2/out0 $R/runs/day2/split $k | head -16
done
