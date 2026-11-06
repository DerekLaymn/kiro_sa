#!/usr/bin/env bash
# Day 10: split the parents into per-purpose groups (copies) under runs/day10/parents/. Adapted from campaign/day9/mk_groups.sh.
# `typediff generate --from-seeds DIR` applies the same --ops/--n to every file in DIR, so the number of programs per
# parent is set by the group it sits in. Idempotent: rebuilds only runs/day10/parents. Plan: campaign/day10-morning.md.
# Differences from Day 9: the operators are the ones with the least use (gradual_injection, union_widen, literal_injection,
# inheritance_diamond, scope_relocation used on one day only; generic_nesting, decorator_wrapping, descriptor_property not
# since Day 8 / Day 7) plus the two Day-9 instruction operators on two parents; the parents sit in the thinnest areas
# (typeddict, final_classvar, abstract_classes, context_managers, gradual_any, paramspec_concatenate, callables); the six
# Day-9 operators that gave 0 or almost 0 live findings (python_version_flip, async_generator_wrap, protocol_vs_abc,
# variance_flip, bound_constraint_swap) get no group; the TY-4900 / MYPY-22360 crash groups are gone (0 escapes on Day 9).
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
G=runs/day10/parents
rm -rf "$G"
mkdir -p "$G"/H_new "$G"/N_flow "$G"/N_types "$G"/N_class "$G"/N_wrap "$G"/O_overload "$G"/C_pyright_range "$G"/C_tvt "$G"/R_reserve
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
rput() {  # rput GROUP AREA FILE : copy a Day-9 generated program (runs/day9/gen/AREA/FILE.py) as rsv_AREA_<hash>.py
  src="runs/day9/gen/$2/$3.py"
  h=$(echo "$3" | sed 's/.*_\([0-9a-f]\{8\}\)$/\1/')
  if [ -f "$src" ]; then cp "$src" "$G/$1/rsv_$2_$h.py"; else echo "mk_groups: missing reserve parent $src" >&2; FAIL=1; fi
}

# ---- Day-9 instruction operators (typediff/operators.py), second round on the two promoted parents only
# H_new: d8p_* (Day 9 promotion, area dunder_dispatch) and d9p_* (promoted this morning, area context_managers)
put H_new d8p_dunder_dispatch_annotation_only_call
put H_new d9p_context_managers_swallowed_name_possibly_unbound

# ---- operators with the least use, each on 8 parents where it has something to move (24 programs per group)
# N_flow: scope_relocation 2 + gradual_injection 1. Parents with flow-sensitive narrowing, forward references, `with`.
put N_flow d4v_ty_alias_loop_backedge
put N_flow d4v_ty_flag_or_else_never
put N_flow s3r1_ty_type_equality_narrowing_any
put N_flow s3r1_mypy_class_base_forward_ref
hput N_flow narrowing_user conformance__narrowing_typeis
hput N_flow narrowing_user conformance__narrowing_typeguard
hput N_flow narrowing_user pyright__typeIs3
hput N_flow gradual_any conformance__exceptions_context_managers
# N_types: union_widen 1 + literal_injection 2. Parents in the thinnest areas (typeddict, final_classvar, overloads).
# d3p_generics_callable_attr_contravariant is the Day-9 "revisit" parent (0 live in its 3 Day-9 mutants; 3 live on Days 7 and 8):
# this is its test with two operators it has not had (a retired-if-0-again decision for the Day-11 morning).
sput N_types typeddict readonly_notrequired
hput N_types final_classvar pyright__final3
sput N_types overloads literal_flag_overload
hput N_types typeddict conformance__typeddicts_required
hput N_types typeddict pyright__typedDict10
hput N_types final_classvar pyright__final2
hput N_types final_classvar mypy__check_final__testFinalDefiningInstanceVar
put N_types d3p_generics_callable_attr_contravariant
# N_class: inheritance_diamond 2 + descriptor_property 1. Parents with overrides, several bases, Self, metaclass calls.
hput N_class inheritance_mro conformance__classes_override
hput N_class inheritance_mro pyright__mro2
hput N_class inheritance_mro pyright__methodOverride2
hput N_class abstract_classes mypy__check_abstract__testImplementingAbstractMethodWithMultipleBaseClasses
hput N_class abstract_classes pyright__abstractClass5
hput N_class constructors_metaclasses conformance__constructors_call_metaclass
hput N_class self_classmethods conformance__generics_self_basic
sput N_class self_classmethods self_classmethod_param
# N_wrap: decorator_wrapping 1 + generic_nesting 2. Parents with callables, decorators, ParamSpec.
sput N_wrap paramspec_concatenate decorator_signature
hput N_wrap callables conformance__callables_subtyping
hput N_wrap callables conformance__callables_kwargs
hput N_wrap callables conformance__callables_annotation
hput N_wrap paramspec_concatenate conformance__generics_paramspec_components
hput N_wrap paramspec_concatenate conformance__generics_paramspec_semantics
hput N_wrap generics_variance conformance__generics_upper_bound
put N_wrap d3p_callables_partial_too_many_positional

# ---- overload_reorder (Day 9: 0.88 live per program, the best of the six old operators) on three overload parents it did not have
hput O_overload overloads conformance__overloads_consistency
hput O_overload overloads conformance__overloads_evaluation
hput O_overload overloads conformance__overloads_definitions

# ---- crash families that still reproduce (campaign/day10/phase2/results/crash-parents-probe.tsv): the pyright RangeError
# parent that stays (its sibling d5p_..one_decorator.. was retired this morning) and the TypeVarTuple + ParamSpec default parent
put C_pyright_range d5p_descriptors_decorated_get_pyright_rangeerror
put C_tvt d3p_typevartuple_unpack_paramspec_default_after_tvt
# NOT copied anywhere: the draft-1 expanding-receiver family (ty rc 134, no KB entry), the ty crash parents closed by an
# entry (TY-4148 / 4882 / 4898 / 4899 / 4900, 0 escapes on Days 8 and 9), d6p_..mypy_subscript and d5p_..one_decorator..
# (retired today), d3p_crash_mypy_segv_recursive_tvt_default_alias (mypy rc 137, MYPY-22361).

# ---- pass-2 reserve: Day-9 programs with a live finding on the Day-10 KB that is not in a family already filed, closed or
# queued for the KB (campaign/day10-morning.md section 5). 6 parents x 4 programs = 24.
rput R_reserve context_managers gen5_c8eb51b8
rput R_reserve context_managers gen15_d3110ded
rput R_reserve generics_variance rsv_generics_variance_7ffc3316__mut0_3c28536f
rput R_reserve paramspec_concatenate paramspec_concatenate__decorator_signature__mut1_29247984
rput R_reserve abstract_classes rsv_abstract_classes_5a90804c__mut0_cf2683fb
rput R_reserve gradual_any gen6_76921a4b

for d in "$G"/*/; do printf '%s %s\n' "$(basename "$d")" "$(ls "$d" | wc -l)"; done
printf 'hits %s\n' "$(ls runs/hits/*.py | wc -l)"
[ "$FAIL" = 0 ] || { echo "mk_groups: FAILED (missing inputs above)" >&2; exit 1; }
