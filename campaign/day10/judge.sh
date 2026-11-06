#!/usr/bin/env bash
# Day 10 judge + triage (Plan §3 daily loop steps 2-3). Deterministic: no LLM. Run from anywhere, after the generation
# is complete (gen_pass.sh: written=250, pending=0). Judged WITH --pyright-only on ALL programs, as on Days 7 to 9:
# pyright errors that mypy and ty both miss, where CPython ran the statement, become `only_pyright` findings.
# kbloop_stats prints `live=` (with) and `live without only_pyright:` (comparable with Days 1 to 6). The last step counts
# `only_pyright` findings by runtime relation (`runtime_supports` is the one to read).
# Usage: judge.sh [GEN_DIR] [OUT_DIR]   (default runs/day10/gen runs/day10/out)
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
PY=$ROOT/.venv/bin/python
TD=$ROOT/.venv/bin/typediff
GEN="${1:-runs/day10/gen}"
OUT="${2:-runs/day10/out}"
cd "$ROOT" || exit 1
export TYPEDIFF_LLM=null
s=$(date +%s)
$PY scripts/kbloop_run.py "$OUT" "$GEN" --jobs 14 --pyright-only --progress "$OUT-progress.log" > "$OUT-run.log" 2>&1
echo "kbloop_run exit=$? secs=$(( $(date +%s) - s ))" > campaign/day10/judge.done
$PY scripts/kbloop_stats.py "$OUT" > campaign/day10-stats.txt 2>&1
$TD --out "$OUT" triage "$OUT" --top 30 --details > campaign/day10-triage.txt 2>&1
$PY campaign/day10/only_pyright_relations.py "$OUT" > campaign/day10-only-pyright-relations.txt 2>&1
echo "stats+triage+relations exit=$? total_secs=$(( $(date +%s) - s ))" >> campaign/day10/judge.done
