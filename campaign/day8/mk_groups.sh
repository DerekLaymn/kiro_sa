#!/usr/bin/env bash
# Day 8: split the parents into per-purpose groups (copies) under runs/day8/parents/. Adapted from campaign/day7/mk_groups.sh.
# `typediff generate --from-seeds DIR` applies the same --ops/--n to every file in DIR, so the number of programs per
# parent is set by the group it sits in. Idempotent: rebuilds only runs/day8/parents. Plan: campaign/day8-morning.md.
# Differences from Day 7: a parent is looked up in runs/hits and then runs/hits-dropped (retired parents still crash
# ty), a missing parent is an error (Day 7 `cp` failed silently), reserve parents come from the Day-7 generated programs.
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
G=runs/day8/parents
rm -rf "$G"
mkdir -p "$G"/A_ty_4898 "$G"/A_pyright_range "$G"/A_ty_escape "$G"/H_new "$G"/P_pyright \
         "$G"/R_reserve3 "$G"/R_reserve2 "$G"/N_seeds_a "$G"/N_seeds_b
FAIL=0

put() {  # put GROUP NAME : copy runs/hits/NAME.py or runs/hits-dropped/NAME.py
  for d in runs/hits runs/hits-dropped; do
    if [ -f "$d/$2.py" ]; then cp "$d/$2.py" "$G/$1/" && return 0; fi
  done
  echo "mk_groups: missing parent $2" >&2; FAIL=1
}
rput() {  # rput GROUP AREA FILE : copy a Day-7 generated program (runs/day7/gen/AREA/FILE.py) as rsv_AREA_<hash>.py
  src="runs/day7/gen/$2/$3.py"
  h=$(echo "$3" | sed 's/.*_\([0-9a-f]\{8\}\)$/\1/')
  if [ -f "$src" ]; then cp "$src" "$G/$1/rsv_$2_$h.py"; else echo "mk_groups: missing reserve parent $src" >&2; FAIL=1; fi
}
sput() {  # sput GROUP DIR FILE : copy a hand seed as DIR__FILE
  src="seeds/$2/$3.py"
  if [ -f "$src" ]; then cp "$src" "$G/$1/$2__$3.py"; else echo "mk_groups: missing seed $src" >&2; FAIL=1; fi
}

# ---- (c) crash families that still reproduce (campaign/day8/phase2/crash-parents-probe.tsv)
put A_ty_4898 d3p_paramspec_identity_applied_to_itself                       # ty rc 134 stack overflow, TY-4898
put A_pyright_range d5p_descriptors_decorated_get_pyright_rangeerror          # pyright rc 2 RangeError (draft 7)
put A_pyright_range d5p_descriptors_one_decorator_dunders_pyright_rangeerror  # pyright rc 2 RangeError (draft 7)
# retired parents (runs/hits-dropped) that still crash ty: "escape watch", 2 programs each, other ops than Day 7
put A_ty_escape d3p_callables_self_call_attr                                  # TY-4148, rc 134
put A_ty_escape d4v_callables_mutual_call_attr                                # TY-4148, rc 134
put A_ty_escape d3p_self_classmethods_self_call_union                         # TY-4148, rc 134
put A_ty_escape d3p_protocols_generic_protocol_stack_overflow                 # TY-4882, rc 134 (not the draft-1 receiver shape)
# NOT copied anywhere: d3p_paramspec_self_annotated_dunder_call (Day 7: 0 of 7 mutants crash; its findings are all
# dismissed since Day 8 phase 1), the draft-1 expanding-receiver family and d6p_async_generators_protocol_flatten_overflow_ty.

# ---- promoted on Day 7, never mutated yet
put H_new d7p_tuples_unpacking_partial_unpack_except_ty

# ---- pyright-leaning parents (decorated descriptors: the only family with an only_pyright runtime_supports so far)
put P_pyright d3p_descriptors_decorated_get
put P_pyright d4p_descriptors_readonly_prop_never
put P_pyright d3p_generics_callable_attr_contravariant

# ---- pass-2 reserve: Day-7 programs of the no-parent areas with a live finding that is not a KB-queued family
# (campaign/day8-morning.md section 4). 8 parents x 3 programs + 1 parent x 2 programs = 26.
# gen9_c53ea70f (mypy join `list[Sequence[object]]` vs ty/pyright union) was considered and left out: join-vs-union is
# a "do not chase" item of the plan.
rput R_reserve3 overloads gen7_d41747bd
rput R_reserve3 overloads gen4_7ab4b09b
rput R_reserve3 abstract_classes gen9_ae31b752
rput R_reserve3 tuples_unpacking tuples_unpacking__variadic_tuples__mut0_b068dfad
rput R_reserve3 tuples_unpacking tuples_unpacking__variadic_tuples__mut1_c98fed28
rput R_reserve3 dataclasses dataclasses__overloaded_post_init__mut0_223fff8f
rput R_reserve3 recursive_aliases gen4_0bbabab4
rput R_reserve3 recursive_aliases gen3_d5395259
rput R_reserve2 overloads gen9_d6e90b34

# ---- hand seeds of the areas without a parent. N_seeds_a: the two seeds whose Day-7 mutants gave the repeating
# families (13 + 11 live) get 2 programs; N_seeds_b: the others get 4 (self_classmethods was not seeded on Day 7).
sput N_seeds_a match_statement class_sequence_patterns
sput N_seeds_a dataclasses overloaded_post_init
sput N_seeds_a final_classvar final_overrides
sput N_seeds_b dataclasses kw_only_initvar_order
sput N_seeds_b dataclasses dataclass_transform
sput N_seeds_b typeddict readonly_notrequired
sput N_seeds_b overloads literal_flag_overload
sput N_seeds_b tuples_unpacking variadic_tuples
sput N_seeds_b self_classmethods self_classmethod_param
sput N_seeds_b self_classmethods self_param_inherited
sput N_seeds_b self_classmethods self_runtime_witness

for d in "$G"/*/; do printf '%s %s\n' "$(basename "$d")" "$(ls "$d" | wc -l)"; done
printf 'hits %s\n' "$(ls runs/hits/*.py | wc -l)"
[ "$FAIL" = 0 ] || { echo "mk_groups: FAILED (missing inputs above)" >&2; exit 1; }
