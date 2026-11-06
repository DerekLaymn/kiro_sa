#!/usr/bin/env bash
# Day 10 generation: 250 programs, INCLUDING one pass-2 reserve of 24 programs (plan and breakdown: campaign/day10-morning.md).
# Day 10 prefers the NEWEST areas (context_managers, dunder_dispatch, then the thinnest old ones: final_classvar,
# abstract_classes, typeddict, gradual_any, paramspec_concatenate) and the operators with the LEAST use (gradual_injection,
# union_widen, literal_injection, inheritance_diamond, scope_relocation: one day each; generic_nesting, decorator_wrapping,
# descriptor_property: none since Day 8 / Day 7) over the exhausted families: match_statement, recursive_aliases,
# dataclasses, tuples_unpacking and enums_literals get no fresh program, async_generators and descriptors_properties
# appear only through parents; the Day-9 operators with 0 live findings get no group.
# The reserve parents are Day-9 programs that already showed a live finding, so no mid-day judge is needed.
# Expected final count: written=250.
# Usage: gen_pass.sh [pass_number]. Idempotent: a re-run only re-emits prompts for missing answers (file bridge)
# and recounts pending/written. Run campaign/day10/mk_groups.sh first.
PASS="${1:-0}"
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
TD=$ROOT/.venv/bin/typediff
# Dry-run overrides (campaign/day10/gen-pass-dryrun.sh): DAY10_INBOX, DAY10_OUT, DAY10_GATE, DAY10_LOG, DAY10_RETRIES, DAY10_SLEEP.
INBOX=${DAY10_INBOX:-$ROOT/runs/day10/inbox}
OUT=${DAY10_OUT:-runs/day10/gen}
LOG=${DAY10_LOG:-campaign/day10/gen-pass.log}
G=runs/day10/parents
cd "$ROOT" || exit 1
export PYTHONHASHSEED=0
unset TYPEDIFF_LLM
mkdir -p "$INBOX" "$OUT"

run() {  # retry up to 3 times on failure (network/TLS)
  for i in $(seq 1 "${DAY10_RETRIES:-3}"); do "$@" && return 0; echo "retry $i: $*"; sleep "${DAY10_SLEEP:-5}"; done
  return 0
}
gen_seeds() {  # gen_seeds GROUP OP N
  run $TD --llm file:$INBOX --python-version 3.13 generate --from-seeds "$G/$1" --n "$3" --ops "$2" --out-dir "$OUT"
}
gen_area() {  # gen_area AREA N
  run $TD --llm file:$INBOX --python-version 3.13 generate --area "$1" --n "$2" --out-dir "$OUT"
}
# Operators and n differ from Days 3 to 9 for every parent and area, on purpose: the file bridge keys a prompt by its
# text, and an identical prompt would only reproduce an earlier program (campaign/day10/phase2/scripts/overlap_prior.sh).

# ---- Day-9 instruction operators, second round on the two promoted parents: 6 + 6 = 12
gen_seeds H_new exit_swallow_flip 3              # 2 parents x 3
gen_seeds H_new dunder_instance_shadow 3

# ---- operators with the least use, 4 groups x 8 parents x 3 = 96
gen_seeds N_flow scope_relocation 2              # 8 parents x 2
gen_seeds N_flow gradual_injection 1             # 8 parents x 1
gen_seeds N_types union_widen 1                  # n differs from Day 8 (literal_injection 1 on the same seeds had the same prompt keys)
gen_seeds N_types literal_injection 2
gen_seeds N_class inheritance_diamond 2
gen_seeds N_class descriptor_property 1
gen_seeds N_wrap decorator_wrapping 1            # n differs from Day 7 (decorator_wrapping 2 on a generics parent had the same keys)
gen_seeds N_wrap generic_nesting 2

# ---- overload_reorder on three parents it did not have: 9
gen_seeds O_overload overload_reorder 3

# ---- crash families: 6 + 4 = 10
gen_seeds C_pyright_range descriptor_property 1  # 1 parent x 6 (n=3 of both operators was Day 6, n=2 Day 7)
gen_seeds C_pyright_range decorator_wrapping 1
gen_seeds C_pyright_range scope_relocation 2
gen_seeds C_pyright_range union_widen 1          # union_widen 2 on this parent was Day 8
gen_seeds C_pyright_range gradual_injection 1
gen_seeds C_tvt generic_nesting 2                # 1 parent x 4
gen_seeds C_tvt union_widen 1
gen_seeds C_tvt gradual_injection 1

# ---- pass-2 reserve: 6 parents x 4 = 24 (Day-9 programs with a live finding)
gen_seeds R_reserve scope_relocation 1
gen_seeds R_reserve union_widen 1
gen_seeds R_reserve literal_injection 1
gen_seeds R_reserve gradual_injection 1

# ---- fresh programs, the two newest areas: 18 + 8 = 26
gen_area context_managers 18
gen_area dunder_dispatch 8
# ---- fresh programs, the thinnest old areas and the areas with few programs on Days 7 to 9: 73
gen_area final_classvar 5                        # n=6 was Day 8
gen_area abstract_classes 8                      # n=9 was Day 8
gen_area typeddict 6
gen_area gradual_any 8
gen_area callables 5
gen_area paramspec_concatenate 6
gen_area inheritance_mro 5
gen_area self_classmethods 5
gen_area constructors_metaclasses 5
gen_area overloads 5
gen_area protocols 4
gen_area generics_variance 4
gen_area narrowing_user 4
gen_area typevartuple_unpack 3                   # n=4 was Day 6

PENDING=0
for p in "$INBOX"/*.prompt.md; do
  [ -e "$p" ] || continue
  k=$(basename "$p" .prompt.md)
  [ -e "$INBOX/$k.answer.json" ] || PENDING=$((PENDING+1))
done
WRITTEN=$(find "$OUT" -type f -name '*.py' | wc -l)
echo "- gen pass $PASS: pending=$PENDING written=$WRITTEN" | tee -a "$LOG"
GATE=${DAY10_GATE:-/home/derek/Projects/5th_sem/Software_analysis/Assignment/Assignment_2/.agents/tasks/day10-gen-status.json}
mkdir -p "$(dirname "$GATE")"
printf '{"pass": %s, "pending": %s, "written": %s}\n' "$PASS" "$PENDING" "$WRITTEN" > "$GATE"
$ROOT/.venv/bin/python scripts/inbox_check.py "$INBOX"
