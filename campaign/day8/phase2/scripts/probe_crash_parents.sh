#!/usr/bin/env bash
# Day 8 morning (Plan §3 "Every morning"): which crash-family parents still crash the pinned tools?
# Same method as campaign/day7/partB/probe_ty_crash_parents.sh (sequential, memguard shim in .venv/bin, 90 s limit),
# extended to the retired crash parents in runs/hits-dropped and to the one mypy crash parent.
# Output TSV on stdout: file, location (hits|hits-dropped), tool, rc, signature.
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
V=$ROOT/.venv/bin
sig() {  # sig OUTPUT
  case "$1" in
    *"overflowed its stack"*|*"stack overflow"*|*"SIGABRT"*) echo stack-overflow;;
    *"too many cycle iterations"*|*"panicked"*|*"panic"*) echo panic;;
    *"memguard"*|*"memory"*) echo memguard;;
    *"RangeError"*|*"Maximum call stack"*) echo rangeerror;;
    *) echo -;;
  esac
}
printf 'file\tloc\ttool\trc\tsignature\n'
for b in d3p_callables_self_call_attr d4v_callables_mutual_call_attr d3p_self_classmethods_self_call_union \
         d3p_paramspec_identity_applied_to_itself d3p_paramspec_self_annotated_dunder_call \
         d3p_protocols_generic_protocol_stack_overflow d6p_async_generators_protocol_flatten_overflow_ty \
         d4v_protocols_expanding_self_receiver d3p_crash_ty_stack_overflow_protocol_flatten \
         d3p_crash_ty_panic_partial_or_none_in_loop d3p_crash_ty_timeout_typeis_generic_in_loop \
         d4p_callables_crash_ty_panic_partial_loop d4v_ty_alias_loop_backedge d3p_recursive_aliases_type_of_self_alias \
         d3p_typevartuple_unpack_paramspec_default_after_tvt d6p_typevartuple_unpack_pep695_paramspec_default_mypy_subscript \
         d3p_generics_typevar_default_refers_to_itself d3p_generics_contravariant_recursive_base; do
  if [ -f "runs/hits/$b.py" ]; then loc=hits; f="runs/hits/$b.py"
  elif [ -f "runs/hits-dropped/$b.py" ]; then loc=hits-dropped; f="runs/hits-dropped/$b.py"
  else printf '%s\t-\t-\t-\tmissing\n' "$b"; continue; fi
  o=$(timeout 90 $V/ty check --python-version 3.13 "$f" 2>&1); rc=$?
  o="${o//$b/}"
  printf '%s\t%s\tty\t%s\t%s\n' "$b" "$loc" "$rc" "$(sig "$o")"
done
# the mypy crash parent (MYPY-22361 family)
b=d3p_crash_mypy_segv_recursive_tvt_default_alias
f=runs/hits/$b.py
o=$(timeout 90 $V/mypy --python-version 3.13 --no-incremental "$f" 2>&1); rc=$?
printf '%s\thits\tmypy\t%s\t%s\n' "$b" "$rc" "$(sig "$o")"
# the pyright RangeError parents (draft 7)
for b in d5p_descriptors_decorated_get_pyright_rangeerror d5p_descriptors_one_decorator_dunders_pyright_rangeerror; do
  f=runs/hits/$b.py
  o=$(timeout 90 $V/pyright --pythonversion 3.13 "$f" 2>&1); rc=$?
  printf '%s\thits\tpyright\t%s\t%s\n' "$b" "$rc" "$(sig "$o")"
done
