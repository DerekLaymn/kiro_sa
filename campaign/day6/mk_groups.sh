#!/usr/bin/env bash
# Day 6: split runs/hits into per-purpose parent groups (copies) under runs/day6/parents/.
# `typediff generate --from-seeds DIR` applies the same --ops/--n to every file in DIR, so per-parent
# op counts are controlled by which group a parent sits in. Idempotent: rebuilds the group dirs.
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
G=runs/day6/parents
rm -rf "$G"
mkdir -p "$G"/A_ty_crash "$G"/M_mypy_crash "$G"/P_pyright "$G"/C_callback "$G"/R_rest

A="d3p_callables_self_call_attr d4v_callables_mutual_call_attr d3p_self_classmethods_self_call_union
d3p_protocols_generic_protocol_stack_overflow d4v_protocols_expanding_self_receiver
d6p_async_generators_protocol_flatten_overflow_ty d6p_protocols_expanding_self_receiver_pep695_ty
d3p_paramspec_identity_applied_to_itself d3p_paramspec_self_annotated_dunder_call"
M="d3p_generics_contravariant_recursive_base d3p_generics_typevar_default_refers_to_itself
d3p_crash_mypy_segv_recursive_tvt_default_alias d3p_recursive_aliases_type_of_self_alias"
P="d5p_descriptors_decorated_get_pyright_rangeerror d5p_descriptors_one_decorator_dunders_pyright_rangeerror
d3p_descriptors_decorated_get d4p_descriptors_readonly_prop_never d3p_generics_callable_attr_contravariant"
C="d6p_typevartuple_unpack_pep695_paramspec_default_mypy_subscript d3p_typevartuple_unpack_paramspec_default_after_tvt"

for f in $A; do cp "runs/hits/$f.py" "$G/A_ty_crash/"; done
for f in $M; do cp "runs/hits/$f.py" "$G/M_mypy_crash/"; done
for f in $P; do cp "runs/hits/$f.py" "$G/P_pyright/"; done
for f in $C; do cp "runs/hits/$f.py" "$G/C_callback/"; done
for f in runs/hits/*.py; do
  b=$(basename "$f" .py)
  ALL=$(printf '%s ' $A $M $P $C)
  case " $ALL" in *" $b "*) ;; *) cp "$f" "$G/R_rest/";; esac
done
for d in "$G"/*/; do printf '%s %s\n' "$(basename "$d")" "$(ls "$d" | wc -l)"; done
printf 'hits %s\n' "$(ls runs/hits/*.py | wc -l)"
