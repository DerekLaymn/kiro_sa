#!/usr/bin/env bash
# Day 8 judge + triage (Plan §3 daily loop steps 2-3). Deterministic: no LLM. Run from anywhere, after the generation
# is complete (gen_pass.sh: written=250, pending=0). Judged WITH --pyright-only on ALL programs, as on Day 7: pyright
# errors that mypy and ty both miss, where CPython ran the statement, become `only_pyright` findings. kbloop_stats prints
# `live=` (with) and `live without only_pyright:` (comparable with Days 1 to 6). With the Day-8 harness, an only_pyright
# finding whose statement raised a handled type exception is `runtime_supports`; the last step counts them (priority (c)).
# Usage: judge.sh [GEN_DIR] [OUT_DIR]   (default runs/day8/gen runs/day8/out)
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
PY=$ROOT/.venv/bin/python
TD=$ROOT/.venv/bin/typediff
GEN="${1:-runs/day8/gen}"
OUT="${2:-runs/day8/out}"
cd "$ROOT" || exit 1
export TYPEDIFF_LLM=null
s=$(date +%s)
$PY scripts/kbloop_run.py "$OUT" "$GEN" --jobs 14 --pyright-only --progress "$OUT-progress.log" > "$OUT-run.log" 2>&1
echo "kbloop_run exit=$? secs=$(( $(date +%s) - s ))" > campaign/day8/judge.done
$PY scripts/kbloop_stats.py "$OUT" > campaign/day8-stats.txt 2>&1
$TD --out "$OUT" triage "$OUT" --top 30 --details > campaign/day8-triage.txt 2>&1
$PY campaign/day8/only_pyright_relations.py "$OUT" > campaign/day8-only-pyright-relations.txt 2>&1
echo "stats+triage+relations exit=$? total_secs=$(( $(date +%s) - s ))" >> campaign/day8/judge.done
