cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
bash /tmp/d8/replay7.sh
bash /tmp/d8/replay_old.sh
bash /tmp/d8/supports.sh
P=campaign/day8/phase1
echo "== live paramspec family: Day 7 after / Day 6 after"
.venv/bin/python /tmp/d8/live.py runs/day8/day7replay self_annotated_dunder_call | tail -1
.venv/bin/python /tmp/d8/live.py runs/day7/day6replay-pyright self_annotated_dunder_call | tail -1
.venv/bin/python /tmp/d8/live.py runs/day8/day6replay self_annotated_dunder_call | tail -1
.venv/bin/python /tmp/d8/live.py runs/day7/out self_annotated_dunder_call | tail -1
