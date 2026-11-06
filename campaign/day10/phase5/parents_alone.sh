#!/usr/bin/env bash
# Day 10 phase 5 (Plan §3 "retire patterns you have classified"): run every mutated parent of runs/hits ALONE on the Day-10 KB
# (own input dir, --jobs 4, --pyright-only), so parent_signatures.py can compare the live findings of the mutants with the
# live findings of their parent. Read-only on runs/hits. Output dir /tmp/d10p5/parents-out.
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
export TYPEDIFF_LLM=null
W=/tmp/d10p5/parents
rm -rf "$W" /tmp/d10p5/parents-out; mkdir -p "$W"
awk 'NR>1 && $2=="hits" {print $1}' campaign/day10/phase5/parent_yield.out > campaign/day10/phase5/hits_parents.txt
while read -r p; do
  cp "runs/hits/$p.py" "$W/"
done < campaign/day10/phase5/hits_parents.txt
ls "$W" | wc -l
timeout 900 .venv/bin/python scripts/kbloop_run.py /tmp/d10p5/parents-out "$W" --jobs 4 --pyright-only --progress /tmp/d10p5/parents-prog.log > /tmp/d10p5/parents-run.log 2>&1
echo "kbloop_run rc=$?"
.venv/bin/python scripts/kbloop_stats.py /tmp/d10p5/parents-out 2>&1 | head -3
