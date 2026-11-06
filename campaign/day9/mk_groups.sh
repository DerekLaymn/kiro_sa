#!/usr/bin/env bash
# Day 9: split the parents into per-purpose groups (copies) under runs/day9/parents/. Adapted from campaign/day8/mk_groups.sh.
# `typediff generate --from-seeds DIR` applies the same --ops/--n to every file in DIR, so the number of programs per
# parent is set by the group it sits in. Idempotent: rebuilds only runs/day9/parents. Plan: campaign/day9-morning.md.
# Differences from Day 8: parents come from five places (runs/hits, runs/hits-dropped, seeds/, seeds/harvested/, the
# Day-8 generated programs for the reserve); the parents are chosen for the Day-9 operators, not for a crash family
# (the escape-watch group of Day 8 is gone, the ParamSpec parents stay retired).
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
G=runs/day9/parents
rm -rf "$G"
mkdir -p "$G"/H_dunder "$G"/D_shadow "$G"/D_exit "$G"/O_overload "$G"/O_generics "$G"/O_protocol "$G"/O_version \
         "$G"/O_async "$G"/C_generic_rec "$G"/C_pyright_range "$G"/C_tvt "$G"/R_reserve
FAIL=0

put() {  # put GROUP NAME : copy runs/hits/NAME.py or runs/hits-dropped/NAME.py
  for d in runs/hits runs/hits-dropped; do
    if [ -f "$d/$2.py" ]; then cp "$d/$2.py" "$G/$1/" && return 0; fi
  done
  echo "mk_groups: missing parent $2" >&2; FAIL=1
}
sput() {  # sput GROUP DIR FILE : copy a hand seed as DIR__FILE
  src="seeds/$2/$3.py"
  if [ -f "$src" ]; then cp "$src" "$G/$1/$2__$3.py"; else echo "mk_groups: missing seed $src" >&2; FAIL=1; fi
}
hput() {  # hput GROUP AREA FILE : copy a harvested conformance/mypy/pyright program as hv_AREA__FILE
  src="seeds/harvested/$2/$3.py"
  if [ -f "$src" ]; then cp "$src" "$G/$1/hv_$2__$3.py"; else echo "mk_groups: missing harvested $src" >&2; FAIL=1; fi
}
rput() {  # rput GROUP AREA FILE : copy a Day-8 generated program (runs/day8/gen/AREA/FILE.py) as rsv_AREA_<hash>.py
  src="runs/day8/gen/$2/$3.py"
  h=$(echo "$3" | sed 's/.*_\([0-9a-f]\{8\}\)$/\1/')
  if [ -f "$src" ]; then cp "$src" "$G/$1/rsv_$2_$h.py"; else echo "mk_groups: missing reserve parent $src" >&2; FAIL=1; fi
}

# ---- NEW operator dunder_instance_shadow / exit_swallow_flip (Day 9 phase 1, typediff/operators.py)
# H_dunder: the program promoted this morning (d8p_*, annotation-only __call__), the area dunder_dispatch has no other parent
put H_dunder d8p_dunder_dispatch_annotation_only_call
# D_shadow: 7 parents that already define or look up special methods (descriptors, metaclass operators, ordering, callbacks)
put D_shadow d3p_descriptors_decorated_get
put D_shadow d4v_metaclass_reflected_op
put D_shadow d3p_inheritance_mro_total_ordering_inherited_lt
sput D_shadow callables positional_only_assignability
sput D_shadow constructors_metaclasses new_returns_other
sput D_shadow inheritance_mro override_lsp
hput D_shadow protocols conformance__protocols_class_objects
# D_exit: 7 parents with exceptional control flow, narrowing or Self-returning methods (what a `with` block changes)
put D_exit d7p_tuples_unpacking_partial_unpack_except_ty
put D_exit d4v_ty_attr_eq_narrow_unreachable
put D_exit d3p_narrowing_user_index_assign_stale
sput D_exit narrowing_builtin len_in_walrus
sput D_exit narrowing_user typeis_generic
sput D_exit gradual_any gradual_guarantee
sput D_exit self_classmethods self_runtime_witness

# ---- the six operators that were never used on Days 3 to 8 (variance_flip, bound_constraint_swap, protocol_vs_abc,
# overload_reorder, python_version_flip, async_generator_wrap): each goes to parents where it has something to flip
sput O_overload overloads literal_flag_overload
sput O_overload descriptors_properties descriptor_get_overload
hput O_overload overloads mypy__check_classes__testOverloadedDescriptorSelected
hput O_overload overloads conformance__overloads_basic
sput O_generics generics_variance constrained_typevar
sput O_generics generics_variance pep695_variance_inference
sput O_generics generics_variance typevar_defaults
sput O_generics paramspec_concatenate decorator_signature
put O_generics d3p_generics_callable_attr_contravariant
put O_generics d3p_generics_typevar_default_refers_to_itself
sput O_protocol protocols generic_callback_protocol
sput O_protocol protocols property_vs_attribute
hput O_protocol protocols conformance__protocols_explicit
hput O_version gradual_any conformance__directives_version_platform
hput O_version gradual_any pyright__staticExpression1
hput O_version gradual_any pyright__unreachable1
sput O_async async_generators generator_send_return
hput O_async async_generators pyright__generator11
hput O_async async_generators pyright__async1

# ---- crash families that still reproduce on ty 0.0.97 or crash another tool (campaign/day9/phase2/results/crash-parents-probe.tsv)
# C_generic_rec: ty rc 134 (TY-4900, retired Day 4 as a near duplicate, not probed on Day 8) + the mypy MYPY-22360 sibling
put C_generic_rec d3p_generics_contravariant_recursive_generic_base
put C_generic_rec d3p_generics_contravariant_recursive_base
# C_pyright_range: pyright rc 2 RangeError (draft 7), 12 programs on Day 8, all rediscoveries: smaller share, other operators
put C_pyright_range d5p_descriptors_decorated_get_pyright_rangeerror
put C_pyright_range d5p_descriptors_one_decorator_dunders_pyright_rangeerror
# C_tvt: the TypeVarTuple + ParamSpec default parents (mypy crash family of draft 5, ty gives diagnostics)
put C_tvt d3p_typevartuple_unpack_paramspec_default_after_tvt
put C_tvt d6p_typevartuple_unpack_pep695_paramspec_default_mypy_subscript
# NOT copied anywhere: the draft-1 expanding-receiver family (ty rc 134, no KB entry: generating from it recreates the
# Day-6 live crash findings), d3p_callables_self_call_attr / d4v_callables_mutual_call_attr /
# d3p_self_classmethods_self_call_union / d3p_protocols_generic_protocol_stack_overflow (Day 8 escape watch: 7 of 8
# programs crashed and every crash was closed, 0 escapes), the two ParamSpec parents (retired Day 8).

# ---- pass-2 reserve: Day-8 programs of non-exhausted areas with a live finding in the replay with the Day-9 KB
# (campaign/day9-morning.md section 4). 6 parents x 4 programs = 24.
rput R_reserve generics_variance d3p_generics_callable_attr_contravariant__mut1_7ffc3316
rput R_reserve abstract_classes rsv_abstract_classes_ae31b752__mut0_5a90804c
rput R_reserve descriptors_properties gen9_92c10e28
rput R_reserve descriptors_properties gen1_4287130f
rput R_reserve self_classmethods gen10_22a2e020
rput R_reserve overloads rsv_overloads_d6e90b34__mut0_186f739e

for d in "$G"/*/; do printf '%s %s\n' "$(basename "$d")" "$(ls "$d" | wc -l)"; done
printf 'hits %s\n' "$(ls runs/hits/*.py | wc -l)"
[ "$FAIL" = 0 ] || { echo "mk_groups: FAILED (missing inputs above)" >&2; exit 1; }
