#!/usr/bin/env bash
# Syntax check of the Day-10 generation scripts and a diff against the Day-9 files they were adapted from.
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
for f in campaign/day10/*.sh campaign/day10/phase2/scripts/*.sh; do bash -n "$f" && echo "ok  $f" || echo "BAD $f"; done
for f in campaign/day10/*.py campaign/day10/phase2/scripts/*.py; do
  .venv/bin/python -m py_compile "$f" && echo "ok  $f" || echo "BAD $f"
done
for f in gen_worker.sh answer_pending.sh judge.sh gen-pass-dryrun.sh only_pyright_relations.py check_reserve.py \
         operator_follow.py check_gen_sessions.py live_by_area.py; do
  echo "--- diff $f (day9 vs day10)"; diff "campaign/day9/$f" "campaign/day10/$f"
done
echo "--- stale day9 / d9 paths in day10 scripts (expect only comments naming Day 9)"
grep -n "day9\|d9\|DAY9" campaign/day10/*.sh campaign/day10/*.py
