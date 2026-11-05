#!/usr/bin/env bash
# Day 7 judge + triage (Plan §3 daily loop steps 2-3). Deterministic: no LLM. Run from anywhere, after the
# generation passes are complete. Judged WITH --pyright-only: pyright errors that mypy and ty both miss, where
# CPython ran the statement, become `only_pyright` findings. They are listed separately in the report; the
# live counts of Days 1 to 6 do not include them (those runs used the default).
# Usage: judge.sh [GEN_DIR] [OUT_DIR]   (default runs/day7/gen runs/day7/out)
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
PY=$ROOT/.venv/bin/python
TD=$ROOT/.venv/bin/typediff
GEN="${1:-runs/day7/gen}"
OUT="${2:-runs/day7/out}"
cd "$ROOT" || exit 1
export TYPEDIFF_LLM=null
s=$(date +%s)
$PY scripts/kbloop_run.py "$OUT" "$GEN" --jobs 14 --pyright-only --progress "$OUT-progress.log" > "$OUT-run.log" 2>&1
echo "kbloop_run exit=$? secs=$(( $(date +%s) - s ))" > campaign/day7/judge.done
$PY scripts/kbloop_stats.py "$OUT" > campaign/day7-stats.txt 2>&1
$TD --out "$OUT" triage "$OUT" --top 30 --details > campaign/day7-triage.txt 2>&1
echo "stats+triage exit=$? total_secs=$(( $(date +%s) - s ))" >> campaign/day7/judge.done
