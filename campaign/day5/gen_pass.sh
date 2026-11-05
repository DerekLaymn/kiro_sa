#!/usr/bin/env bash
# Day 5 generation pass (run from anywhere; cd's to repo root). Usage: gen_pass.sh [pass_number]
# Idempotent: re-running only re-emits prompts for missing answers and recounts pending/written.
PASS="${1:-0}"
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
TD=$ROOT/.venv/bin/typediff
INBOX=$ROOT/runs/day5/inbox
GATE=/home/derek/Projects/5th_sem/Software_analysis/Assignment/Assignment_2/.agents/tasks/day5-gen-status.json
cd "$ROOT" || exit 1
export PYTHONHASHSEED=0
unset TYPEDIFF_LLM
mkdir -p "$INBOX" runs/day5/gen

run() {  # retry up to 3 times on failure (network/TLS)
  for i in 1 2 3; do "$@" && return 0; echo "retry $i: $*"; sleep 5; done
  return 0
}

# P2: seed-based mutation
for OP in narrowing_construct_swap runtime_witness; do
  run $TD --llm file:$INBOX --python-version 3.13 generate --from-seeds runs/hits --n 1 --ops $OP --out-dir runs/day5/gen
done
# n=2: each prompt carries a 'Variant k of n' line (Day-5 step 1b) so the two variants differ
for OP in feature_crossover; do
  run $TD --llm file:$INBOX --python-version 3.13 generate --from-seeds runs/hits --n 2 --ops $OP --out-dir runs/day5/gen
done

# P3: areas not covered on Day 3
for AREA in overloads protocols dataclasses typevartuple_unpack enums_literals; do
  run $TD --llm file:$INBOX --python-version 3.13 generate --area $AREA --n 10 --out-dir runs/day5/gen
done

PENDING=0
for p in "$INBOX"/*.prompt.md; do
  [ -e "$p" ] || continue
  k=$(basename "$p" .prompt.md)
  [ -e "$INBOX/$k.answer.json" ] || PENDING=$((PENDING+1))
done
WRITTEN=$(find runs/day5/gen -type f -name '*.py' | wc -l)

echo "- gen pass $PASS: pending=$PENDING written=$WRITTEN" >> campaign/day5-run-log.md
mkdir -p "$(dirname "$GATE")"
printf '{"pass": %s, "pending": %s, "written": %s}\n' "$PASS" "$PENDING" "$WRITTEN" > "$GATE"
echo "pass=$PASS pending=$PENDING written=$WRITTEN"
