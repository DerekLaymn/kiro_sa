#!/usr/bin/env bash
# Day 4 judge + triage (Plan §3 daily loop steps 2-3). Deterministic: no LLM. Run from anywhere.
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
PY=$ROOT/.venv/bin/python
TD=$ROOT/.venv/bin/typediff
cd "$ROOT" || exit 1
export TYPEDIFF_LLM=null
s=$(date +%s)
$PY scripts/kbloop_run.py runs/day4/out runs/day4/gen --jobs 14 --progress runs/day4/out-progress.log > runs/day4/out-run.log 2>&1
echo "kbloop_run exit=$? secs=$(( $(date +%s) - s ))" > campaign/day4/judge.done
$PY scripts/kbloop_stats.py runs/day4/out > campaign/day4-stats.txt 2>&1
$TD --out runs/day4/out triage runs/day4/out --top 30 --details > campaign/day4-triage.txt 2>&1
echo "stats+triage exit=$? total_secs=$(( $(date +%s) - s ))" >> campaign/day4/judge.done
