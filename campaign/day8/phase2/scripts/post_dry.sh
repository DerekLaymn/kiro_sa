#!/usr/bin/env bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
echo "== real inbox/gen exist?"; ls -d runs/day8/inbox runs/day8/gen 2>&1
echo "== gate files"; ls -la /home/derek/Projects/5th_sem/Software_analysis/Assignment/Assignment_2/.agents/tasks/ 2>&1 | grep -i day8
echo "== reserve check"; cat campaign/day8/phase2/reserve-check.out
echo "== prompts per group (count of unique prompt keys by first words is not available); distinct prompt texts:"
cat /tmp/d8-dryrun/inbox/*.prompt.md | wc -c
ls /tmp/d8-dryrun/inbox/*.prompt.md | wc -l
echo "== git status"; git status --short
