#!/usr/bin/env bash
export TYPEDIFF_LLM=null
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R || exit 1
$R/.venv/bin/python -m pytest /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/tests -q > campaign/s3-r1-pytest.txt 2>&1
echo "exit=$?" >> campaign/s3-r1-pytest.txt
