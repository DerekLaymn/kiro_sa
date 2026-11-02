#!/usr/bin/env bash
export TYPEDIFF_LLM=null
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R || exit 1
$R/.venv/bin/python campaign/tmp/calib3_compare.py > campaign/s3-r3-calib-compare.txt 2>&1
$R/.venv/bin/python -m pytest /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/tests -q > campaign/s3-r3-pytest.txt 2>&1
echo "exit=$?" >> campaign/s3-r3-pytest.txt
$R/.venv/bin/typediff --python-version 3.13 kb-selftest > campaign/s3-r3-kb-selftest-final.txt 2>&1
echo "exit=$?" >> campaign/s3-r3-kb-selftest-final.txt
$R/.venv/bin/python scripts/kbloop_patterns.py runs/day2/out3 --set tuning --top 30 --md campaign/s3-r3-patterns-after-tuning.md > campaign/s3-r3-patterns-after-tuning.txt 2>&1
$R/.venv/bin/python scripts/kbloop_patterns.py runs/day2/out3 --set holdout --top 15 > campaign/s3-r3-patterns-after-holdout.txt 2>&1
date > campaign/s3-r3-final-checks.done
