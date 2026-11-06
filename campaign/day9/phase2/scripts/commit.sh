#!/usr/bin/env bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
git branch --show-current
git status --short --untracked-files=all campaign/day9 | grep -v "^?? campaign/day9/phase1" | head -80
echo "--- pycache?"
git status --short --untracked-files=all | grep -i pycache
find campaign/day9 -name __pycache__ -type d -prune -exec rm -rf {} +
git add campaign/day9-morning.md campaign/day9-run-log.md campaign/day9
git status --short | grep -v "^??"
git commit -q -m "docs: day 9 phase 2 morning plan (promote dunder parent, 250-program plan with new areas and operators, day 9 scripts; dry run pending=250)" && echo committed
git log --oneline | head -3
git status --short
