#!/usr/bin/env bash
# Day 6 generation pass: 200 mutated + 50 fresh = 250 programs (plan: campaign/day6-morning.md).
# Run from anywhere. Usage: gen_pass.sh [pass_number]. Idempotent: a re-run only re-emits prompts for
# missing answers (file bridge) and recounts pending/written. Run campaign/day6/mk_groups.sh first.
PASS="${1:-0}"
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
TD=$ROOT/.venv/bin/typediff
INBOX=$ROOT/runs/day6/inbox
OUT=runs/day6/gen
G=runs/day6/parents
cd "$ROOT" || exit 1
export PYTHONHASHSEED=0
unset TYPEDIFF_LLM
mkdir -p "$INBOX" "$OUT"

run() {  # retry up to 3 times on failure (network/TLS)
  for i in 1 2 3; do "$@" && return 0; echo "retry $i: $*"; sleep 5; done
  return 0
}
gen_seeds() {  # gen_seeds GROUP OP N
  run $TD --llm file:$INBOX --python-version 3.13 generate --from-seeds "$G/$1" --n "$3" --ops "$2" --out-dir "$OUT"
}
gen_area() {  # gen_area AREA N
  run $TD --llm file:$INBOX --python-version 3.13 generate --area "$1" --n "$2" --out-dir "$OUT"
}

# A: 9 ty crash parents x 7 = 63
gen_seeds A_ty_crash recursion_deepening 3
gen_seeds A_ty_crash feature_crossover 3
gen_seeds A_ty_crash invalid_type_form 1
# M: 4 mypy crash parents x 4 = 16
gen_seeds M_mypy_crash recursion_deepening 2
gen_seeds M_mypy_crash feature_crossover 1
gen_seeds M_mypy_crash invalid_type_form 1
# P: 5 pyright-pass parents x 9 = 45
gen_seeds P_pyright decorator_wrapping 3
gen_seeds P_pyright descriptor_property 3
gen_seeds P_pyright generic_nesting 3
# C: 2 Callback-shape parents x 9 = 18
gen_seeds C_callback feature_crossover 4
gen_seeds C_callback generic_nesting 3
gen_seeds C_callback invalid_type_form 2
# R: 29 other parents x 2 = 58
gen_seeds R_rest narrowing_construct_swap 1
gen_seeds R_rest runtime_witness 1

# fresh: 50 programs
gen_area descriptors_properties 12
gen_area paramspec_concatenate 12
gen_area callables 8
gen_area protocols 8
gen_area recursive_aliases 6
gen_area typevartuple_unpack 4

PENDING=0
for p in "$INBOX"/*.prompt.md; do
  [ -e "$p" ] || continue
  k=$(basename "$p" .prompt.md)
  [ -e "$INBOX/$k.answer.json" ] || PENDING=$((PENDING+1))
done
WRITTEN=$(find "$OUT" -type f -name '*.py' | wc -l)
echo "- gen pass $PASS: pending=$PENDING written=$WRITTEN" | tee -a campaign/day6/gen-pass.log
