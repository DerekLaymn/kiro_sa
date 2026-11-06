#!/usr/bin/env bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
P=campaign/day8/phase2
.venv/bin/python $P/scripts/area_live.py runs/day7/out runs/day8/day7replay-it2 runs/day7/gen > $P/area-live-table.txt 2>&1
.venv/bin/python $P/scripts/area_live.py runs/day7/out runs/day8/day7replay-it2 runs/day7/gen match_statement dataclasses > $P/area-live-match-dataclasses.txt 2>&1
wc -l $P/area-live-table.txt $P/area-live-match-dataclasses.txt
