#!/bin/bash
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd $K || exit 1
git branch --show-current
git add campaign/day9/phase6 campaign/day9-verification.md campaign/day3-issue-drafts.md campaign/day9-run-log.md
git status --short
git commit -m "docs: day 9 phase 6 verification (8 strong candidates: 1 new, 5 duplicate, 2 not a bug; drafts 9 and 10)"
git log --oneline | head -3
git status --short
