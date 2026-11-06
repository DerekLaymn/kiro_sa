cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
P=campaign/day8/phase1
mkdir -p runs/day8
echo "== Day 6 (baseline: runs/day7/day6replay-pyright, Day-7 KB with --pyright-only)"
rm -rf runs/day8/day6replay
TYPEDIFF_LLM=null .venv/bin/python scripts/kbloop_replay.py runs/day7/day6replay-pyright runs/day8/day6replay --jobs 14 --pyright-only --verify-sample 30 > $P/replay-day6.out 2>&1
echo rc=$?; tail -2 $P/replay-day6.out
.venv/bin/python campaign/day7/partA/replay_diff.py runs/day7/day6replay-pyright runs/day8/day6replay > $P/replay-day6-diff.txt 2>&1
tail -4 $P/replay-day6-diff.txt
.venv/bin/python scripts/kbloop_stats.py runs/day7/day6replay-pyright | head -6 > $P/stats-day6-before.txt 2>&1
.venv/bin/python scripts/kbloop_stats.py runs/day8/day6replay | head -6 > $P/stats-day6-after.txt 2>&1
for n in 3 4 5; do
  echo "== Day $n control (baseline runs/day7/ctrl-day$n)"
  rm -rf runs/day8/ctrl-day$n
  TYPEDIFF_LLM=null .venv/bin/python scripts/kbloop_replay.py runs/day7/ctrl-day$n runs/day8/ctrl-day$n --jobs 14 > $P/replay-day$n.out 2>&1
  echo rc=$?; tail -1 $P/replay-day$n.out
  .venv/bin/python campaign/day7/partA/replay_diff.py runs/day7/ctrl-day$n runs/day8/ctrl-day$n > $P/replay-day$n-diff.txt 2>&1
  tail -3 $P/replay-day$n-diff.txt
done
