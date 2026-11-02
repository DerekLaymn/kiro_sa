#!/usr/bin/env bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
wc -l typediff/*.py
grep -n '^def m_\|^def \|Entry(' typediff/kb.py | head -150
ls tests
ls calibration/negatives
ls calibration
which gh; gh auth status 2>&1 | head -5
