#!/usr/bin/env bash
# Day 8 generation: 250 programs, INCLUDING the 26-program pass-2 reserve (plan and breakdown: campaign/day8-morning.md).
# Day 7 generated only 224 of 250 and never spent the reserve. The Day-8 reserve parents are Day-7 programs that
# already showed a live finding, so no mid-day judge is needed and the reserve is the last section of this script.
# Expected final count: written=250.
# Usage: gen_pass.sh [pass_number]. Idempotent: a re-run only re-emits prompts for missing answers (file bridge)
# and recounts pending/written. Run campaign/day8/mk_groups.sh first.
PASS="${1:-0}"
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
TD=$ROOT/.venv/bin/typediff
# Dry-run overrides (campaign/day8/gen-pass-dryrun.sh): DAY8_INBOX, DAY8_OUT, DAY8_GATE, DAY8_LOG, DAY8_RETRIES, DAY8_SLEEP.
INBOX=${DAY8_INBOX:-$ROOT/runs/day8/inbox}
OUT=${DAY8_OUT:-runs/day8/gen}
LOG=${DAY8_LOG:-campaign/day8/gen-pass.log}
G=runs/day8/parents
cd "$ROOT" || exit 1
export PYTHONHASHSEED=0
unset TYPEDIFF_LLM
mkdir -p "$INBOX" "$OUT"

run() {  # retry up to 3 times on failure (network/TLS)
  for i in $(seq 1 "${DAY8_RETRIES:-3}"); do "$@" && return 0; echo "retry $i: $*"; sleep "${DAY8_SLEEP:-5}"; done
  return 0
}
gen_seeds() {  # gen_seeds GROUP OP N
  run $TD --llm file:$INBOX --python-version 3.13 generate --from-seeds "$G/$1" --n "$3" --ops "$2" --out-dir "$OUT"
}
gen_area() {  # gen_area AREA N
  run $TD --llm file:$INBOX --python-version 3.13 generate --area "$1" --n "$2" --out-dir "$OUT"
}
# Operators and n differ from Day 7 for the same parent/area on purpose: the file bridge keys a prompt by its text, and
# an identical prompt would only reproduce the Day-7 program.

# ---- (c) crash families that still reproduce: 28 mutants + 12 fresh = 40
# TY-4898 identity parent: 1 parent x 8
gen_seeds A_ty_4898 recursion_deepening 4
gen_seeds A_ty_4898 feature_crossover 3
gen_seeds A_ty_4898 invalid_type_form 1
# pyright RangeError pair (draft 7): 2 parents x 6 = 12 (runtime_witness: CPython evidence for only_pyright)
gen_seeds A_pyright_range runtime_witness 2
gen_seeds A_pyright_range inheritance_diamond 2
gen_seeds A_pyright_range union_widen 2
# retired parents that still crash ty (TY-4148 trio, TY-4882): escape watch, 4 parents x 2 = 8
gen_seeds A_ty_escape feature_crossover 1
gen_seeds A_ty_escape generic_nesting 1
gen_area recursive_aliases 12

# ---- pass-2 reserve: 26 = 8 parents x 3 + 1 parent x 2 (mutants of Day-7 programs with a live finding)
gen_seeds R_reserve3 feature_crossover 1
gen_seeds R_reserve3 runtime_witness 1
gen_seeds R_reserve3 narrowing_construct_swap 1
gen_seeds R_reserve2 feature_crossover 1
gen_seeds R_reserve2 runtime_witness 1

# ---- pyright-leaning, only_pyright runtime_supports: 18 mutants (judge with --pyright-only, judge.sh does)
gen_seeds P_pyright runtime_witness 2
gen_seeds P_pyright inheritance_diamond 2
gen_seeds P_pyright scope_relocation 2

# ---- promoted Day-7 parent (partial unpack exception, draft 6): 8
gen_seeds H_new feature_crossover 3
gen_seeds H_new narrowing_construct_swap 2
gen_seeds H_new runtime_witness 2
gen_seeds H_new generic_nesting 1

# ---- areas with no parent (typeddict, overloads, match_statement, dataclasses, self_classmethods, final_classvar,
# abstract_classes) and tuples_unpacking: 120 fresh + 38 seed mutants = 158
gen_area match_statement 24
gen_area dataclasses 24
gen_area typeddict 12
gen_area overloads 14
gen_area self_classmethods 11
gen_area abstract_classes 9
gen_area final_classvar 6
gen_area tuples_unpacking 8
gen_area descriptors_properties 12
# 11 hand seeds: 3 seeds x 2 = 6, 8 seeds x 4 = 32
gen_seeds N_seeds_a union_widen 1
gen_seeds N_seeds_a gradual_injection 1
gen_seeds N_seeds_b qualifier_toggle 1
gen_seeds N_seeds_b literal_injection 1
gen_seeds N_seeds_b annotation_spelling_swap 1
gen_seeds N_seeds_b scope_relocation 1

PENDING=0
for p in "$INBOX"/*.prompt.md; do
  [ -e "$p" ] || continue
  k=$(basename "$p" .prompt.md)
  [ -e "$INBOX/$k.answer.json" ] || PENDING=$((PENDING+1))
done
WRITTEN=$(find "$OUT" -type f -name '*.py' | wc -l)
echo "- gen pass $PASS: pending=$PENDING written=$WRITTEN" | tee -a "$LOG"
GATE=${DAY8_GATE:-/home/derek/Projects/5th_sem/Software_analysis/Assignment/Assignment_2/.agents/tasks/day8-gen-status.json}
mkdir -p "$(dirname "$GATE")"
printf '{"pass": %s, "pending": %s, "written": %s}\n' "$PASS" "$PENDING" "$WRITTEN" > "$GATE"
$ROOT/.venv/bin/python scripts/inbox_check.py "$INBOX"
