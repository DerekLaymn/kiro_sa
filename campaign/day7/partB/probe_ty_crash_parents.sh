#!/usr/bin/env bash
# Day 7 morning: do the crash-family parents chosen for generation still crash ty 0.0.97?
# Sequential, memguard shim in .venv/bin, 90 s limit. Output: TSV on stdout.
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
V=$ROOT/.venv/bin
printf 'file\tty_rc\tsignature\n'
for b in d3p_callables_self_call_attr d4v_callables_mutual_call_attr d3p_self_classmethods_self_call_union \
         d3p_paramspec_identity_applied_to_itself d3p_paramspec_self_annotated_dunder_call \
         d3p_protocols_generic_protocol_stack_overflow d6p_async_generators_protocol_flatten_overflow_ty \
         d4v_protocols_expanding_self_receiver d6p_protocols_expanding_self_receiver_pep695_ty \
         d3p_crash_ty_stack_overflow_protocol_flatten; do
  f="runs/hits/$b.py"
  o=$(timeout 90 $V/ty check --python-version 3.13 "$f" 2>&1); rc=$?
  o="${o//$b/}"
  case "$o" in
    *"overflowed its stack"*|*"stack overflow"*|*"SIGABRT"*) s=stack-overflow;;
    *"too many cycle iterations"*|*"panicked"*|*"panic"*) s=panic;;
    *"memguard"*|*"memory"*) s=memguard;;
    *) s=-;;
  esac
  printf '%s\t%s\t%s\n' "$b" "$rc" "$s"
done
