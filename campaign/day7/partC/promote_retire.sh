#!/usr/bin/env bash
# Day 7 morning decisions after the judge run (Plan §3 "Every morning: promote/retire parents"). Reversible:
#   retire:  mv runs/hits-dropped/<name>.py runs/hits/
#   promote: rm runs/hits/d7p_tuples_unpacking_partial_unpack_except_ty.py  (and git rm --cached)
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
SRC=runs/day7/gen/tuples_unpacking/tuples_unpacking__partial_unpack_exception__mut0_1a265ba6.py
NEW=runs/hits/d7p_tuples_unpacking_partial_unpack_except_ty.py

# ---- promote: header (3 lines, check_hits format) + the program body (lines 7.. of the mutant, the generator's own
# duplicated header comments dropped)
{
  echo "# area: tuples_unpacking"
  echo "# hypothesis: An exception raised by a later unpacking target leaves the earlier target's store in place: CPython reaches the except branch with value == 'bad'. ty 0.0.97 and pyright 1.1.414 reveal Literal[1] there (the multi-target assignment treated as atomic), mypy reveals int | str. Vary: a nested star target, a match/isinstance narrowing in the handler, a for-loop target, an attribute or subscript target as the first element, a finally block, with/del."
  echo "# origin: runs/day7/gen/tuples_unpacking/tuples_unpacking__partial_unpack_exception__mut0_1a265ba6.py (seed-1b309724816f); two sibling mutants (a5e7d2e6, 662f76ab) show the same finding; hand seed seeds/tuples_unpacking/partial_unpack_exception.py"
  sed -n '6,$p' "$SRC"
} > "$NEW"
head -n 8 "$NEW"

# ---- retire: parents whose Day-7 mutants gave only dismissed findings (0 live in 3 to 5 programs each)
mkdir -p runs/hits-dropped
for b in d3p_callables_self_call_attr d4v_callables_mutual_call_attr d3p_self_classmethods_self_call_union \
         d3p_protocols_generic_protocol_stack_overflow; do
  if [ -e "runs/hits/$b.py" ]; then mv "runs/hits/$b.py" "runs/hits-dropped/$b.py" && echo "retired $b"; else echo "missing $b"; fi
done
ls runs/hits/*.py | wc -l
