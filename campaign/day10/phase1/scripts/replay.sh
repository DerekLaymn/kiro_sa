#!/bin/bash
# Replay prior-day reports on the Day-10 KB and diff tier/decided_by per finding.
#   day9: runs/day9/out            (pyright-only run)
#   day8: runs/day9/day8replay     (the Day-9 phase-1 replay of Day 8, so Day-9 changes are not counted again)
#   day7: runs/day7/out            (pyright-only run, harness refreshed with --rerun-runtime)
#   day5: runs/day5/out            (run without --pyright-only, harness refreshed)
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
R=campaign/day10/phase1/results
rm -f $R/replay.done
run() {  # name src flags...
  name=$1; src=$2; shift 2
  dst=runs/day10/replay/$name
  rm -rf "$dst"; mkdir -p runs/day10/replay
  TYPEDIFF_LLM=null timeout 1500 .venv/bin/python scripts/kbloop_replay.py "$src" "$dst" --jobs 8 --verify-sample 30 "$@" > $R/replay-$name.out 2>&1
  echo "replay rc=$?" >> $R/replay-$name.out
  .venv/bin/python campaign/day10/phase1/scripts/diff_replay.py "$src" "$dst" > $R/replay-$name-diff.txt 2>&1
  echo "day done $name" >> $R/replay.status
}
rm -f $R/replay.status
run day9 runs/day9/out --pyright-only
run day8 runs/day9/day8replay --pyright-only
run day7 runs/day7/out --pyright-only --rerun-runtime
run day5 runs/day5/out --rerun-runtime
touch $R/replay.done
