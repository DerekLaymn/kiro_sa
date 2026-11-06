cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
R=campaign/day9/phase2/results
bash campaign/day9/phase2/scripts/syntax.sh > $R/syntax.out 2>&1
bash campaign/day9/gen-pass-dryrun.sh > $R/gen-pass-dryrun.out 2>&1
echo "dryrun rc=$?" >> $R/gen-pass-dryrun.out
bash campaign/day9/phase2/scripts/overlap_prior.sh > $R/overlap-prior.out 2>&1
bash campaign/day9/phase2/scripts/shared_key.sh > $R/shared-key.out 2>&1
.venv/bin/python campaign/day9/check_reserve.py > $R/reserve-check.out 2>&1
.venv/bin/python campaign/day4m/check_hits.py 0.80 > $R/check_hits-final.out 2>&1
echo "check_hits rc=$?" >> $R/check_hits-final.out
git status --short > $R/git-status.out 2>&1
ls runs/day9 runs/day9/inbox runs/day9/gen > $R/runs-day9-listing.out 2>&1
echo "step3 done" > $R/step3.done
