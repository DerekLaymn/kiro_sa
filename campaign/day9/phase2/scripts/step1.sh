cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
R=campaign/day9/phase2/results
bash campaign/day9/phase2/scripts/areas.sh before > $R/step1-before.out 2>&1
bash campaign/day9/phase2/scripts/promote.sh > $R/promote.out 2>&1
bash campaign/day9/phase2/scripts/areas.sh after > $R/step1-after.out 2>&1
