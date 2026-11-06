#!/usr/bin/env bash
# Day 9 generation: 250 programs, INCLUDING one pass-2 reserve of 24 programs (plan and breakdown: campaign/day9-morning.md).
# Day 9 prefers NEW areas (dunder_dispatch, context_managers) and NEW operators (dunder_instance_shadow, exit_swallow_flip,
# and the six old operators no earlier day used) over the exhausted families: match_statement, tuples_unpacking,
# recursive_aliases, dataclasses and typeddict get no fresh program; overloads and descriptors_properties appear only
# through operator groups and the reserve.
# The reserve parents are Day-8 programs that already showed a live finding, so no mid-day judge is needed.
# Expected final count: written=250.
# Usage: gen_pass.sh [pass_number]. Idempotent: a re-run only re-emits prompts for missing answers (file bridge)
# and recounts pending/written. Run campaign/day9/mk_groups.sh first.
PASS="${1:-0}"
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
TD=$ROOT/.venv/bin/typediff
# Dry-run overrides (campaign/day9/gen-pass-dryrun.sh): DAY9_INBOX, DAY9_OUT, DAY9_GATE, DAY9_LOG, DAY9_RETRIES, DAY9_SLEEP.
INBOX=${DAY9_INBOX:-$ROOT/runs/day9/inbox}
OUT=${DAY9_OUT:-runs/day9/gen}
LOG=${DAY9_LOG:-campaign/day9/gen-pass.log}
G=runs/day9/parents
cd "$ROOT" || exit 1
export PYTHONHASHSEED=0
unset TYPEDIFF_LLM
mkdir -p "$INBOX" "$OUT"

run() {  # retry up to 3 times on failure (network/TLS)
  for i in $(seq 1 "${DAY9_RETRIES:-3}"); do "$@" && return 0; echo "retry $i: $*"; sleep "${DAY9_SLEEP:-5}"; done
  return 0
}
gen_seeds() {  # gen_seeds GROUP OP N
  run $TD --llm file:$INBOX --python-version 3.13 generate --from-seeds "$G/$1" --n "$3" --ops "$2" --out-dir "$OUT"
}
gen_area() {  # gen_area AREA N
  run $TD --llm file:$INBOX --python-version 3.13 generate --area "$1" --n "$2" --out-dir "$OUT"
}
# Operators and n differ from Days 3 to 8 for every parent and area, on purpose: the file bridge keys a prompt by its
# text, and an identical prompt would only reproduce an earlier program (campaign/day9/phase2/scripts/overlap_prior.sh).

# ---- NEW operators with their own instruction (typediff/operators.py): 6 + 21 + 21 = 48
# promoted parent d8p_dunder_dispatch_annotation_only_call: 1 parent x 6
gen_seeds H_dunder dunder_instance_shadow 4
gen_seeds H_dunder exit_swallow_flip 2
# D_shadow: 7 parents x 3
gen_seeds D_shadow dunder_instance_shadow 3
# D_exit: 7 parents x 3
gen_seeds D_exit exit_swallow_flip 3

# ---- the six old operators no earlier day used: 8 + 18 + 6 + 6 + 9 = 47
gen_seeds O_overload overload_reorder 2          # 4 parents x 2
gen_seeds O_generics variance_flip 2             # 6 parents x 2
gen_seeds O_generics bound_constraint_swap 1     # 6 parents x 1
gen_seeds O_protocol protocol_vs_abc 2           # 3 parents x 2
gen_seeds O_version python_version_flip 2        # 3 parents x 2
gen_seeds O_async async_generator_wrap 3         # 3 parents x 3

# ---- crash families: 8 + 6 + 8 = 22 (and typevartuple_unpack below is crash-hunting too)
gen_seeds C_generic_rec variance_flip 2          # 2 parents x 4
gen_seeds C_generic_rec recursion_deepening 1
gen_seeds C_generic_rec bound_constraint_swap 1
gen_seeds C_pyright_range dunder_instance_shadow 2   # 2 parents x 3
gen_seeds C_pyright_range overload_reorder 1
gen_seeds C_tvt recursion_deepening 2            # 2 parents x 4
gen_seeds C_tvt invalid_type_form 1
gen_seeds C_tvt bound_constraint_swap 1          # feature_crossover 1 had the same prompt key as a Day-3/4 prompt

# ---- pass-2 reserve: 6 parents x 4 = 24 (Day-8 programs with a live finding)
gen_seeds R_reserve runtime_witness 1
gen_seeds R_reserve feature_crossover 1
gen_seeds R_reserve annotation_spelling_swap 1
gen_seeds R_reserve qualifier_toggle 1

# ---- fresh programs, NEW areas: 22 + 22 = 44
gen_area dunder_dispatch 22
gen_area context_managers 22
# ---- fresh programs, areas with no program on Days 7 and 8: 65
gen_area gradual_any 10
gen_area async_generators 6
gen_area narrowing_builtin 9
gen_area constructors_metaclasses 7
gen_area typevartuple_unpack 8
gen_area narrowing_user 9
gen_area inheritance_mro 7
gen_area protocols 7
gen_area enums_literals 2

PENDING=0
for p in "$INBOX"/*.prompt.md; do
  [ -e "$p" ] || continue
  k=$(basename "$p" .prompt.md)
  [ -e "$INBOX/$k.answer.json" ] || PENDING=$((PENDING+1))
done
WRITTEN=$(find "$OUT" -type f -name '*.py' | wc -l)
echo "- gen pass $PASS: pending=$PENDING written=$WRITTEN" | tee -a "$LOG"
GATE=${DAY9_GATE:-/home/derek/Projects/5th_sem/Software_analysis/Assignment/Assignment_2/.agents/tasks/day9-gen-status.json}
mkdir -p "$(dirname "$GATE")"
printf '{"pass": %s, "pending": %s, "written": %s}\n' "$PASS" "$PENDING" "$WRITTEN" > "$GATE"
$ROOT/.venv/bin/python scripts/inbox_check.py "$INBOX"
