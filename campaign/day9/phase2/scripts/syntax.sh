#!/usr/bin/env bash
# Syntax check of the Day-9 generation scripts and a diff against the Day-8 files they were adapted from.
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
for f in campaign/day9/*.sh campaign/day9/phase2/scripts/*.sh; do bash -n "$f" && echo "ok  $f" || echo "BAD $f"; done
for f in campaign/day9/check_reserve.py campaign/day9/only_pyright_relations.py; do
  .venv/bin/python -m py_compile "$f" && echo "ok  $f" || echo "BAD $f"
done
echo "--- diff gen_worker.sh (day8 vs day9)"; diff campaign/day8/gen_worker.sh campaign/day9/gen_worker.sh
echo "--- diff answer_pending.sh"; diff campaign/day8/answer_pending.sh campaign/day9/answer_pending.sh
echo "--- diff judge.sh"; diff campaign/day8/judge.sh campaign/day9/judge.sh
echo "--- diff only_pyright_relations.py"; diff campaign/day8/only_pyright_relations.py campaign/day9/only_pyright_relations.py
echo "--- diff check_reserve.py"; diff campaign/day8/check_reserve.py campaign/day9/check_reserve.py
echo "--- diff gen-pass-dryrun.sh"; diff campaign/day8/gen-pass-dryrun.sh campaign/day9/gen-pass-dryrun.sh
echo "--- stale day8 / d8 paths in day9 scripts (expect only comments naming Day 8)"
grep -n "day8\|d8\|DAY8" campaign/day9/*.sh campaign/day9/*.py
