#!/bin/bash
# Iteration 2 (review findings): re-run tests and replays, diff against the iteration-1 replays.
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
P=campaign/day8/phase1/iter2
mkdir -p $P runs/day8
echo "== pytest"
.venv/bin/python -m pytest tests -q > $P/pytest.out 2>&1
tail -2 $P/pytest.out
echo "== kb-selftest"
.venv/bin/typediff --python-version 3.13 kb-selftest > $P/kb-selftest.out 2>&1
grep -c PASS $P/kb-selftest.out; grep -c FAIL $P/kb-selftest.out
echo "== Day 7 full (KB + CPython re-run), compare with iteration 1 (runs/day8/day7replay)"
rm -rf runs/day8/day7replay-it2
TYPEDIFF_LLM=null .venv/bin/python scripts/kbloop_replay.py runs/day7/out runs/day8/day7replay-it2 --jobs 14 --pyright-only --rerun-runtime --verify-sample 30 > $P/replay-day7-full.out 2>&1
echo rc=$?
tail -3 $P/replay-day7-full.out
.venv/bin/python campaign/day7/partA/replay_diff.py runs/day8/day7replay runs/day8/day7replay-it2 > $P/replay-day7-vs-iter1-diff.txt 2>&1
tail -6 $P/replay-day7-vs-iter1-diff.txt
.venv/bin/python scripts/kbloop_stats.py runs/day8/day7replay-it2 > $P/stats-day7-full.txt 2>&1
echo "== Day 6 (KB only, --pyright-only), compare with iteration 1 (runs/day8/day6replay)"
rm -rf runs/day8/day6replay-it2
TYPEDIFF_LLM=null .venv/bin/python scripts/kbloop_replay.py runs/day7/day6replay-pyright runs/day8/day6replay-it2 --jobs 14 --pyright-only --verify-sample 30 > $P/replay-day6.out 2>&1
echo rc=$?
tail -3 $P/replay-day6.out
.venv/bin/python campaign/day7/partA/replay_diff.py runs/day8/day6replay runs/day8/day6replay-it2 > $P/replay-day6-vs-iter1-diff.txt 2>&1
tail -6 $P/replay-day6-vs-iter1-diff.txt
.venv/bin/python campaign/day7/partA/replay_diff.py runs/day7/day6replay-pyright runs/day8/day6replay-it2 > $P/replay-day6-vs-day7kb-diff.txt 2>&1
tail -6 $P/replay-day6-vs-day7kb-diff.txt
.venv/bin/python scripts/kbloop_stats.py runs/day8/day6replay-it2 | head -6 > $P/stats-day6.txt 2>&1
for n in 3 4 5; do
  echo "== Day $n control"
  rm -rf runs/day8/ctrl-day$n-it2
  TYPEDIFF_LLM=null .venv/bin/python scripts/kbloop_replay.py runs/day7/ctrl-day$n runs/day8/ctrl-day$n-it2 --jobs 14 > $P/replay-day$n.out 2>&1
  echo rc=$?; tail -1 $P/replay-day$n.out
  .venv/bin/python campaign/day7/partA/replay_diff.py runs/day8/ctrl-day$n runs/day8/ctrl-day$n-it2 > $P/replay-day$n-vs-iter1-diff.txt 2>&1
  tail -3 $P/replay-day$n-vs-iter1-diff.txt
done
echo "== check_hits"
.venv/bin/python campaign/day4m/check_hits.py 0.80 > $P/check_hits.out 2>&1
tail -2 $P/check_hits.out
