#!/usr/bin/env bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
.venv/bin/python campaign/day7/partB/areas_without_hits.py > campaign/day8/phase2/areas-without-hits.txt 2>&1
.venv/bin/python campaign/day4m/check_hits.py 0.80 > campaign/day8/phase2/check_hits-before.out 2>&1
tail -3 campaign/day8/phase2/check_hits-before.out
