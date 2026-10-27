#!/bin/bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
V=.venv/bin
O=.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/typediff_out
$V/pyright --version > $O/pv.txt 2>&1
{ $V/mypy --version; $V/ty --version; $V/python --version; } > $O/mv.txt 2>&1
$V/pytest -q -p no:cacheprovider > $O/pt.txt 2>&1
echo "rc=$?" >> $O/pt.txt
