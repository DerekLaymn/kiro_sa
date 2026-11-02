#!/usr/bin/env bash
export TYPEDIFF_LLM=null
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R || exit 1
$R/.venv/bin/typediff --python-version 3.13 kb-selftest
echo "exit=$?"
