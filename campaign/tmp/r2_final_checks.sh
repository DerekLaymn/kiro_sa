#!/usr/bin/env bash
export TYPEDIFF_LLM=null
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R || exit 1
$R/.venv/bin/python -m pytest /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/tests -q > campaign/s3-r2-pytest.txt 2>&1
echo "exit=$?" >> campaign/s3-r2-pytest.txt
$R/.venv/bin/typediff --python-version 3.13 kb-selftest > campaign/s3-r2-kb-selftest-final.txt 2>&1
echo "exit=$?" >> campaign/s3-r2-kb-selftest-final.txt
date > campaign/s3-r2-final-checks.done
