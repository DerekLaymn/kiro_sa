#!/usr/bin/env bash
# Day 9 phase 5 (Plan §3 "Every morning: promote parents", triage checklist 1 "reproduce alone"): every program of
# runs/day9/gen with a live finding with strong bug evidence (campaign/day9/phase5/strong_live.out) is re-run ALONE
# (own input dir, --jobs 1, --pyright-only), then its similarity to every file of runs/hits is computed.
# Read-only on runs/hits. Output: alone.out.
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
export TYPEDIFF_LLM=null
W=/tmp/d9p5/alone
rm -rf "$W"; mkdir -p "$W"
i=0
while read -r f; do
  [ -z "$f" ] && continue
  i=$((i+1))
  mkdir -p "$W/in$i"
  cp "runs/day9/gen/$f" "$W/in$i/"
  timeout 600 .venv/bin/python scripts/kbloop_run.py "$W/out$i" "$W/in$i" --jobs 1 --pyright-only --progress "$W/prog$i.log" > "$W/run$i.log" 2>&1
  echo "== $i $f rc=$?"
  .venv/bin/python scripts/kbloop_stats.py "$W/out$i" 2>&1 | head -1
  grep -h -E "^\| D|^\| C" "$W"/out$i/seed-*.md
  grep -h -E "strong/verified, supports bug|STACKTRACE" "$W"/out$i/seed-*.md | cut -c1-220
done < campaign/day9/phase5/candidates.txt
echo "== similarity"
.venv/bin/python campaign/day9/phase5/similarity.py
