#!/bin/bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
ls campaign/day8/phase1/ campaign/day8/phase1/scripts
grep -n "replay" campaign/day8-run-log.md | cut -c1-400 | head -20
wc -l campaign/day8-run-log.md
