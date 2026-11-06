#!/usr/bin/env bash
# Day 9 phase 5 morning decisions (Plan §3 "Every morning: retire parents"). Reversible; runs/ is git-ignored:
#   mv runs/hits-dropped/<name>.py runs/hits/
# Retired: d3p_generics_contravariant_recursive_base. Its escape test (group C_generic_rec, 8 programs with its sibling
# d3p_generics_contravariant_recursive_generic_base) gave 0 live findings and 4 crash events, all closed
# (MYPY-22360 x3, TY-4900 x1); day9-morning.md section 10: "if all closed, the next morning drops it".
# Its own 4 mutants (campaign/day9/phase5/parent_yield.out): 0 live, 1 dismissed, 1 crash (DUPLICATE).
# The sibling d3p_generics_contravariant_recursive_generic_base is already in runs/hits-dropped.
# Promoted: none (campaign/day9/phase5/alone.out, similarity rows, and the run log).
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
echo "before: $(ls runs/hits/*.py | wc -l) files in runs/hits, $(ls runs/hits-dropped/*.py | wc -l) in runs/hits-dropped"
mkdir -p runs/hits-dropped
for b in d3p_generics_contravariant_recursive_base; do
  if [ -e "runs/hits/$b.py" ] && [ ! -e "runs/hits-dropped/$b.py" ]; then mv "runs/hits/$b.py" "runs/hits-dropped/$b.py" && echo "retired $b"; else echo "skipped $b"; fi
done
echo "after: $(ls runs/hits/*.py | wc -l) files in runs/hits, $(ls runs/hits-dropped/*.py | wc -l) in runs/hits-dropped"
.venv/bin/python campaign/day4m/check_hits.py 0.80 > campaign/day9/phase5/check_hits-after.out 2>&1
tail -n 4 campaign/day9/phase5/check_hits-after.out
echo "tracked files under runs: $(git ls-files runs | wc -l)"
