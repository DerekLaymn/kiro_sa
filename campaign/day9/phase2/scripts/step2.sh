cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
R=campaign/day9/phase2/results
mkdir -p $R
bash campaign/day9/phase2/scripts/syntax.sh > $R/syntax.out 2>&1
bash campaign/day9/mk_groups.sh > $R/mk_groups.out 2>&1
echo "mk_groups rc=$?" >> $R/mk_groups.out
.venv/bin/python campaign/day9/check_reserve.py > $R/reserve-check.out 2>&1
echo "step2 part A done" > $R/step2a.done
