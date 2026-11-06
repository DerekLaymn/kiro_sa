#!/bin/bash
# Day 10 phase 5: replay stored reports on the KB with MYPY-8595-METACLASS-CALL and diff tier/decided_by per finding.
#   day10: runs/day10/out            (the judge run of this day, pyright-only)
#   day9 : runs/day10/replay/day9    (the Day-9 reports already replayed on the phase-1 KB, so its changes are not counted twice)
#   day8 : runs/day9/day8replay      (as phase 1)
#   day7 : runs/day7/out             (pyright-only run, harness refreshed with --rerun-runtime, as phase 1)
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
R=campaign/day10/phase5/replay
mkdir -p $R
rm -f $R/replay.done $R/replay.status
run() {  # name src flags...
  name=$1; src=$2; shift 2
  dst=runs/day10/replay2/$name
  rm -rf "$dst"; mkdir -p runs/day10/replay2
  TYPEDIFF_LLM=null timeout 1500 .venv/bin/python scripts/kbloop_replay.py "$src" "$dst" --jobs 8 --verify-sample 30 "$@" > $R/replay-$name.out 2>&1
  echo "replay rc=$?" >> $R/replay-$name.out
  .venv/bin/python campaign/day10/phase1/scripts/diff_replay.py "$src" "$dst" > $R/replay-$name-diff.txt 2>&1
  echo "day done $name" >> $R/replay.status
}
run day10 runs/day10/out --pyright-only
run day9 runs/day10/replay/day9 --pyright-only
run day8 runs/day9/day8replay --pyright-only
run day7 runs/day7/out --pyright-only --rerun-runtime
touch $R/replay.done
