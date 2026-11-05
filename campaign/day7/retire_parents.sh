#!/usr/bin/env bash
# Day 7 morning: retire the four parents whose only findings are now dismissed (Part A log, item 12).
# Moves (reversible with mv) from runs/hits to runs/hits-dropped. runs/ is git-ignored.
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
mkdir -p runs/hits-dropped
for b in d4p_narrowing_stale_alias_loop d3p_narrowing_user_attr_narrowing_kept_after_method_call \
         d3p_narrowing_builtin_stale_alias_condition d3p_tuples_unpacking_constant_fold_subclass; do
  if [ -e "runs/hits/$b.py" ]; then mv "runs/hits/$b.py" "runs/hits-dropped/$b.py" && echo "retired $b"; else echo "missing $b"; fi
done
ls runs/hits/*.py | wc -l
