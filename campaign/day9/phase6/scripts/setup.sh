#!/bin/bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
P=campaign/day9/phase6
mkdir -p $P/repro $P/results $P/search $P/scripts
ls campaign/day9/phase5 > $P/results/phase5-ls.txt 2>&1
cp campaign/day9/phase5/strong_live.out $P/results/phase5-strong_live.out
cp campaign/day9/phase5/candidates.txt $P/results/phase5-candidates.txt
echo done
