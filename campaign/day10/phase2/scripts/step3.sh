cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
R=campaign/day10/phase2/results
# nothing may exist under runs/day10/{inbox,gen} or the real gate file before the dry run
ls runs/day10 > $R/runs-day10-before.out 2>&1
ls /home/derek/Projects/5th_sem/Software_analysis/Assignment/Assignment_2/.agents/tasks/day10-gen-status.json >> $R/runs-day10-before.out 2>&1
bash campaign/day10/phase2/scripts/syntax.sh > $R/syntax.out 2>&1
bash campaign/day10/gen-pass-dryrun.sh > $R/gen-pass-dryrun.out 2>&1
echo "dryrun rc=$?" >> $R/gen-pass-dryrun.out
bash campaign/day10/phase2/scripts/overlap_prior.sh > $R/overlap-prior.out 2>&1
bash campaign/day10/phase2/scripts/shared_key.sh > $R/shared-key.out 2>&1
.venv/bin/python campaign/day10/phase2/scripts/budget.py > $R/budget.out 2>&1
.venv/bin/python campaign/day10/check_reserve.py > $R/reserve-check.out 2>&1
.venv/bin/python campaign/day4m/check_hits.py 0.80 > $R/check_hits-final.out 2>&1
echo "check_hits rc=$?" >> $R/check_hits-final.out
git status --short > $R/git-status.out 2>&1
ls runs/day10 runs/day10/inbox runs/day10/gen > $R/runs-day10-listing.out 2>&1
ls /home/derek/Projects/5th_sem/Software_analysis/Assignment/Assignment_2/.agents/tasks/ > $R/gate-dir-listing.out 2>&1
echo "step3 done" > $R/step3.done
