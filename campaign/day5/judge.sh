#!/usr/bin/env bash
# Day 5 judge + triage (Plan §3 daily loop steps 2-3). Deterministic: no LLM. Run from anywhere.
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
PY=$ROOT/.venv/bin/python
TD=$ROOT/.venv/bin/typediff
cd "$ROOT" || exit 1
export TYPEDIFF_LLM=null
s=$(date +%s)
$PY scripts/kbloop_run.py runs/day5/out runs/day5/gen --jobs 14 --progress runs/day5/out-progress.log > runs/day5/out-run.log 2>&1
echo "kbloop_run exit=$? secs=$(( $(date +%s) - s ))" > campaign/day5/judge.done
$PY scripts/kbloop_stats.py runs/day5/out > campaign/day5-stats.txt 2>&1
$TD --out runs/day5/out triage runs/day5/out --top 30 --details > campaign/day5-triage.txt 2>&1
echo "stats+triage exit=$? total_secs=$(( $(date +%s) - s ))" >> campaign/day5/judge.done
