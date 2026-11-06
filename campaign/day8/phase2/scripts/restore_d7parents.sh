#!/usr/bin/env bash
# Repair: an accidental run of campaign/day7/mk_groups.sh (via the Day-7 dry-run script) emptied
# runs/day7/parents/A_ty_4148 and A_ty_protocol_capped, because the retired parents now live in runs/hits-dropped.
# The files were moved, not edited, so copy them back from runs/hits-dropped. Idempotent.
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
G=runs/day7/parents
for f in d3p_callables_self_call_attr d4v_callables_mutual_call_attr d3p_self_classmethods_self_call_union; do
  cp "runs/hits-dropped/$f.py" "$G/A_ty_4148/" && echo "restored A_ty_4148/$f.py"; done
cp runs/hits-dropped/d3p_protocols_generic_protocol_stack_overflow.py "$G/A_ty_protocol_capped/" && echo "restored A_ty_protocol_capped"
for d in "$G"/*/; do echo "$(basename "$d") $(ls "$d" | wc -l)"; done
