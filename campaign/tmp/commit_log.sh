#!/usr/bin/env bash
R=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $R || exit 1
git add campaign/day2-run-log.md
git add campaign/s3-r1-*.txt campaign/s3-r1-patterns-tuning.md
git add campaign/tmp/*.sh campaign/tmp/*.py
git status --short
git commit -m "docs: log stage 3 round 1 (triage, KB changes, replay, calibration)"
git log --oneline -6
