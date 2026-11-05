#!/usr/bin/env bash
# Day 7 generation pass 1: 224 programs of the 250 budget (plan and breakdown: campaign/day7-morning.md).
# The other 26 (no-hit areas) are the pass-2 reserve: mutants of pass-1 programs that show a live finding.
# Expected final count of this pass: written=224.
# Usage: gen_pass.sh [pass_number]. Idempotent: a re-run only re-emits prompts for missing answers (file bridge)
# and recounts pending/written. Run campaign/day7/retire_parents.sh and campaign/day7/mk_groups.sh first.
PASS="${1:-0}"
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
TD=$ROOT/.venv/bin/typediff
# Dry-run overrides (campaign/day7/partB/gen-pass-dryrun.sh): DAY7_INBOX, DAY7_OUT, DAY7_GATE, DAY7_LOG, DAY7_RETRIES.
INBOX=${DAY7_INBOX:-$ROOT/runs/day7/inbox}
OUT=${DAY7_OUT:-runs/day7/gen}
LOG=${DAY7_LOG:-campaign/day7/gen-pass.log}
G=runs/day7/parents
cd "$ROOT" || exit 1
export PYTHONHASHSEED=0
unset TYPEDIFF_LLM
mkdir -p "$INBOX" "$OUT"

run() {  # retry up to 3 times on failure (network/TLS)
  for i in $(seq 1 "${DAY7_RETRIES:-3}"); do "$@" && return 0; echo "retry $i: $*"; sleep "${DAY7_SLEEP:-5}"; done
  return 0
}
gen_seeds() {  # gen_seeds GROUP OP N
  run $TD --llm file:$INBOX --python-version 3.13 generate --from-seeds "$G/$1" --n "$3" --ops "$2" --out-dir "$OUT"
}
gen_area() {  # gen_area AREA N
  run $TD --llm file:$INBOX --python-version 3.13 generate --area "$1" --n "$2" --out-dir "$OUT"
}

# ---- (c) crash families that still crash ty 0.0.97: 32 mutants + 8 fresh = 40
# TY-4148 trio: 3 parents x 5 = 15
gen_seeds A_ty_4148 recursion_deepening 2
gen_seeds A_ty_4148 feature_crossover 2
gen_seeds A_ty_4148 invalid_type_form 1
# ParamSpec pair (TY-4898 / TY-4899): 2 parents x 7 = 14
gen_seeds A_ty_paramspec recursion_deepening 3
gen_seeds A_ty_paramspec feature_crossover 2
gen_seeds A_ty_paramspec invalid_type_form 2
# protocol overflow, CAPPED: 1 parent x 3 = 3 (draft-1 expanding-receiver family incl. the flatten descendant: 0)
gen_seeds A_ty_protocol_capped feature_crossover 2
gen_seeds A_ty_protocol_capped recursion_deepening 1
gen_area recursive_aliases 8

# ---- (d) pyright-leaning: 30 mutants + 30 fresh = 60 (judge these with --pyright-only)
# 5 parents x 6 = 30
gen_seeds P_pyright decorator_wrapping 2
gen_seeds P_pyright descriptor_property 2
gen_seeds P_pyright generic_nesting 2
gen_area descriptors_properties 10
gen_area paramspec_concatenate 10
gen_area inheritance_mro 10

# ---- (b) areas with no parent in runs/hits: 70 fresh + 54 seed mutants = 124 (the other 26 are the pass-2 reserve)
gen_area typeddict 10
gen_area overloads 10
gen_area match_statement 10
gen_area dataclasses 10
gen_area final_classvar 10
gen_area abstract_classes 10
gen_area tuples_unpacking 10
# 9 hand seeds x 6 = 54
gen_seeds N_seeds feature_crossover 2
gen_seeds N_seeds generic_nesting 1
gen_seeds N_seeds narrowing_construct_swap 1
gen_seeds N_seeds runtime_witness 1
gen_seeds N_seeds invalid_type_form 1

PENDING=0
for p in "$INBOX"/*.prompt.md; do
  [ -e "$p" ] || continue
  k=$(basename "$p" .prompt.md)
  [ -e "$INBOX/$k.answer.json" ] || PENDING=$((PENDING+1))
done
WRITTEN=$(find "$OUT" -type f -name '*.py' | wc -l)
echo "- gen pass $PASS: pending=$PENDING written=$WRITTEN" | tee -a "$LOG"
GATE=${DAY7_GATE:-/home/derek/Projects/5th_sem/Software_analysis/Assignment/Assignment_2/.agents/tasks/day7-gen-status.json}
mkdir -p "$(dirname "$GATE")"
printf '{"pass": %s, "pending": %s, "written": %s}\n' "$PASS" "$PENDING" "$WRITTEN" > "$GATE"
$ROOT/.venv/bin/python scripts/inbox_check.py "$INBOX"
