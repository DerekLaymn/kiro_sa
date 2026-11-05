#!/usr/bin/env bash
# Day 7: split the parents into per-purpose groups (copies) under runs/day7/parents/.
# `typediff generate --from-seeds DIR` applies the same --ops/--n to every file in DIR, so the number of
# programs per parent is set by the group it sits in. Idempotent: rebuilds the group dirs.
# Plan: campaign/day7-morning.md. Run after campaign/day7/retire_parents.sh.
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
G=runs/day7/parents
rm -rf "$G"
mkdir -p "$G"/A_ty_4148 "$G"/A_ty_paramspec "$G"/A_ty_protocol_capped "$G"/P_pyright "$G"/N_seeds

# crash families that still crash ty 0.0.97 (campaign/day7/partB/crash-parents-probe.tsv)
for f in d3p_callables_self_call_attr d4v_callables_mutual_call_attr d3p_self_classmethods_self_call_union; do
  cp "runs/hits/$f.py" "$G/A_ty_4148/"; done
for f in d3p_paramspec_identity_applied_to_itself d3p_paramspec_self_annotated_dunder_call; do
  cp "runs/hits/$f.py" "$G/A_ty_paramspec/"; done
# protocol overflow, CAPPED: ONE parent, 3 programs. It is the two-protocol `P1[T2] | P2[T2]` shape (TY-4882), not
# the draft-1 expanding receiver. The draft-1 family (receiver `self: 'Stream[Stream[T]]'`) gets 0 programs: the four
# expanding-receiver parents (d4v_protocols_expanding_self_receiver, d6p_protocols_expanding_self_receiver_*) AND the
# flatten descendant d6p_async_generators_protocol_flatten_overflow_ty (same receiver shape, Day-6 "same root cause")
# are NOT copied anywhere.
for f in d3p_protocols_generic_protocol_stack_overflow; do
  cp "runs/hits/$f.py" "$G/A_ty_protocol_capped/"; done
# pyright-leaning parents (descriptors with decorated dunders, callable attributes)
for f in d5p_descriptors_decorated_get_pyright_rangeerror d5p_descriptors_one_decorator_dunders_pyright_rangeerror \
         d3p_descriptors_decorated_get d4p_descriptors_readonly_prop_never d3p_generics_callable_attr_contravariant; do
  cp "runs/hits/$f.py" "$G/P_pyright/"; done
# hand seeds of the areas that have no parent in runs/hits yet (abstract_classes has no seed)
for d in typeddict overloads dataclasses final_classvar match_statement tuples_unpacking; do
  for f in seeds/$d/*.py; do cp "$f" "$G/N_seeds/${d}__$(basename "$f")"; done
done
for d in "$G"/*/; do printf '%s %s\n' "$(basename "$d")" "$(ls "$d" | wc -l)"; done
printf 'hits %s\n' "$(ls runs/hits/*.py | wc -l)"
