#!/usr/bin/env bash
# Day 8 phase 5 morning decisions (Plan §3 "Every morning: retire parents"). Reversible; runs/ is git-ignored:
#   mv runs/hits-dropped/<name>.py runs/hits/
# Retired: parents whose mutants give only dismissed findings (campaign/day8/phase5/parent_yield.out):
#   d3p_paramspec_identity_applied_to_itself: Day 8 8 programs, 0 live, 8 dismissed (8 ty crashes, all TY-4898)
#   d3p_paramspec_self_annotated_dunder_call: Day-7 mutants with the final KB, 7 programs, 0 live, 17 dismissed
# Promoted: none (campaign/day8/phase5/alone.out, similarity rows, and the run log).
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
echo "before: $(ls runs/hits/*.py | wc -l) files in runs/hits"
mkdir -p runs/hits-dropped
for b in d3p_paramspec_identity_applied_to_itself d3p_paramspec_self_annotated_dunder_call; do
  if [ -e "runs/hits/$b.py" ]; then mv "runs/hits/$b.py" "runs/hits-dropped/$b.py" && echo "retired $b"; else echo "missing $b"; fi
done
echo "after: $(ls runs/hits/*.py | wc -l) files in runs/hits, $(ls runs/hits-dropped/*.py | wc -l) in runs/hits-dropped"
.venv/bin/python campaign/day4m/check_hits.py 0.80 > campaign/day8/phase5/check_hits-after.out 2>&1
tail -n 4 campaign/day8/phase5/check_hits-after.out
git ls-files runs | wc -l
