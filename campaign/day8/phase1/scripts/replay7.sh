cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
P=campaign/day8/phase1
rm -rf runs/day8/day7replay-kb runs/day8/day7replay
mkdir -p runs/day8
echo "== A: KB only (stored runtime results, no CPython re-run)"
TYPEDIFF_LLM=null .venv/bin/python scripts/kbloop_replay.py runs/day7/out runs/day8/day7replay-kb --jobs 14 --pyright-only --verify-sample 30 > $P/replay-day7-kb.out 2>&1
echo rc=$?
tail -3 $P/replay-day7-kb.out
.venv/bin/python campaign/day7/partA/replay_diff.py runs/day7/out runs/day8/day7replay-kb > $P/replay-day7-kb-diff.txt 2>&1
tail -4 $P/replay-day7-kb-diff.txt
.venv/bin/python scripts/kbloop_stats.py runs/day8/day7replay-kb > $P/stats-day7-kb.txt 2>&1
echo "== B: KB + CPython re-run with the Day-8 harness"
TYPEDIFF_LLM=null .venv/bin/python scripts/kbloop_replay.py runs/day7/out runs/day8/day7replay --jobs 14 --pyright-only --rerun-runtime --verify-sample 30 > $P/replay-day7-full.out 2>&1
echo rc=$?
tail -3 $P/replay-day7-full.out
.venv/bin/python campaign/day7/partA/replay_diff.py runs/day8/day7replay-kb runs/day8/day7replay > $P/replay-day7-runtime-diff.txt 2>&1
tail -4 $P/replay-day7-runtime-diff.txt
.venv/bin/python scripts/kbloop_stats.py runs/day8/day7replay > $P/stats-day7-full.txt 2>&1
