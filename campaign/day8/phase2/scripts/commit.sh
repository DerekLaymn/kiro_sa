#!/usr/bin/env bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
git add campaign/day8-morning.md campaign/day8-run-log.md campaign/day8/mk_groups.sh campaign/day8/gen_pass.sh \
  campaign/day8/answer_pending.sh campaign/day8/gen_worker.sh campaign/day8/judge.sh campaign/day8/gen-pass-dryrun.sh \
  campaign/day8/check_reserve.py campaign/day8/only_pyright_relations.py campaign/day8/phase2
git status --short
git commit -m "docs: day 8 phase 2 morning decisions and generation plan (250 programs incl. 26-program reserve), campaign/day8 scripts, dry run pending=250" 2>&1 | tail -3
git log --oneline | head -2
git status --short
