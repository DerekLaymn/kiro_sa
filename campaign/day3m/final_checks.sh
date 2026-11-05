#!/bin/bash
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R
date > campaign/day3m/final_checks.start
$R/.venv/bin/python -m pytest $R/tests -q -p no:cacheprovider > campaign/day3m/pytest.txt 2>&1
echo "exit $?" >> campaign/day3m/pytest.txt
$R/.venv/bin/typediff --python-version 3.13 kb-selftest > campaign/day3m/kb-selftest.txt 2>&1
echo "exit $?" >> campaign/day3m/kb-selftest.txt
date > campaign/day3m/final_checks.done
