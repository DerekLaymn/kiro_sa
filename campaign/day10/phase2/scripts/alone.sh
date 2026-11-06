#!/usr/bin/env bash
# Day 10 morning (Plan §3 "Every morning: promote parents", triage checklist 1 "reproduce alone"): every candidate of
# campaign/day10/phase2/scripts/candidates.txt (the 8 strong-evidence programs of Day 9 plus the 2 programs of draft 10)
# is re-run ALONE (own input dir, --jobs 1, --pyright-only) on the Day-10 code and KB, then its similarity to every file
# of runs/hits is computed. Read-only on runs/hits. Output: alone.out.
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
export TYPEDIFF_LLM=null
W=/tmp/d10p2/alone
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
done < campaign/day10/phase2/scripts/candidates.txt
echo "== similarity"
.venv/bin/python campaign/day10/phase2/scripts/similarity.py
