#!/usr/bin/env bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
P=campaign/day8/phase2
.venv/bin/python $P/scripts/area_live.py runs/day7/out runs/day8/day7replay-it2 runs/day7/gen overloads tuples_unpacking abstract_classes recursive_aliases generics_variance inheritance_mro | tail -n +17 > $P/area-live-other.txt 2>&1
wc -l $P/area-live-other.txt
