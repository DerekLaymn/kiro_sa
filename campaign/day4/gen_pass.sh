#!/usr/bin/env bash
# Day 4 generation pass (run from anywhere; cd's to repo root). Usage: gen_pass.sh [pass_number]
PASS="${1:-0}"
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
TD=$ROOT/.venv/bin/typediff
INBOX=$ROOT/runs/day4/inbox
GATE=/home/derek/Projects/5th_sem/Software_analysis/Assignment/Assignment_2/.agents/tasks/day4-gen-status.json
cd "$ROOT" || exit 1
export PYTHONHASHSEED=0
unset TYPEDIFF_LLM

run() {  # retry up to 3 times on failure (network/TLS)
  for i in 1 2 3; do "$@" && return 0; echo "retry $i: $*"; sleep 5; done
  return 0
}

# P2: seed-based mutation
for OP in narrowing_construct_swap runtime_witness; do
  run $TD --llm file:$INBOX --python-version 3.13 generate --from-seeds runs/hits --n 1 --ops $OP --out-dir runs/day4/gen
done
for OP in feature_crossover; do
  run $TD --llm file:$INBOX --python-version 3.13 generate --from-seeds runs/hits --n 2 --ops $OP --out-dir runs/day4/gen
done

# P3: areas not covered on Day 3
for AREA in overloads protocols dataclasses typevartuple_unpack enums_literals; do
  run $TD --llm file:$INBOX --python-version 3.13 generate --area $AREA --n 10 --out-dir runs/day4/gen
done

PENDING=0
for p in "$INBOX"/*.prompt.md; do
  [ -e "$p" ] || continue
  k=$(basename "$p" .prompt.md)
  [ -e "$INBOX/$k.answer.json" ] || PENDING=$((PENDING+1))
done
WRITTEN=$(find runs/day4/gen -type f -name '*.py' | wc -l)

echo "- gen pass $PASS: pending=$PENDING written=$WRITTEN" >> campaign/day4-run-log.md
mkdir -p "$(dirname "$GATE")"
printf '{"pass": %s, "pending": %s, "written": %s}\n' "$PASS" "$PENDING" "$WRITTEN" > "$GATE"
echo "pass=$PASS pending=$PENDING written=$WRITTEN"
