#!/usr/bin/env bash
# Replay the Day-10 round (250 generated programs) WITHOUT an LLM.
#
#   scripts/replay_final_round.sh [WORK_DIR]        default WORK_DIR: runs/replay-final-round (git-ignored)
#   JOBS=4 PYTHON=python3 scripts/replay_final_round.sh
#
# 1. The 250 stored model answers (examples/replay/final-round/answers) are put into a file-bridge inbox.
# 2. `typediff generate` is run with the same parents, operators and counts as on Day 10. It writes one prompt per request;
#    the prompt key is a hash of the prompt text, so every request finds its stored answer and the same programs come out.
# 3. The deterministic judge (TYPEDIFF_LLM=null, mypy + ty + pyright + CPython, KB and rules) runs on the programs.
#
# The answers were written by claude-haiku-5.5 (effort medium) and are the only non-deterministic input of the round; see
# docs/generation.md. The judge needs the pinned tool versions (`typediff doctor`).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || PY=python
export TYPEDIFF_TOOL_MEM_MB="${TYPEDIFF_TOOL_MEM_MB:-2048}"   # per mypy / ty process; 0 = unlimited (docs/reproducibility.md)
JOBS="${JOBS:-4}"
if [ "$JOBS" -gt 6 ]; then JOBS=6; fi
WORK="${1:-runs/replay-final-round}"
SRC=examples/replay/final-round
TD=("$PY" -m typediff.cli --python-version 3.13)

rm -rf "$WORK/inbox" "$WORK/gen" "$WORK/out"
mkdir -p "$WORK/inbox" "$WORK/gen"
cp "$SRC"/answers/*.answer.json "$WORK/inbox/"
GEN=("${TD[@]}" --llm "file:$WORK/inbox" generate --out-dir "$WORK/gen")

echo "== 1/3 generation from stored answers"
# parent group, operator, variants per parent (the groups of docs/generation.md)
while read -r group op n; do
  "${GEN[@]}" --from-seeds "$SRC/parents/$group" --ops "$op" --n "$n" > /dev/null
done <<'EOF'
C_pyright_range decorator_wrapping 1
C_pyright_range descriptor_property 1
C_pyright_range gradual_injection 1
C_pyright_range scope_relocation 2
C_pyright_range union_widen 1
C_tvt generic_nesting 2
C_tvt gradual_injection 1
C_tvt union_widen 1
H_new dunder_instance_shadow 3
H_new exit_swallow_flip 3
N_class descriptor_property 1
N_class inheritance_diamond 2
N_flow gradual_injection 1
N_flow scope_relocation 2
N_types literal_injection 2
N_types union_widen 1
N_wrap decorator_wrapping 1
N_wrap generic_nesting 2
O_overload overload_reorder 3
R_reserve gradual_injection 1
R_reserve literal_injection 1
R_reserve scope_relocation 1
R_reserve union_widen 1
EOF
# fresh programs: area, programs
while read -r area n; do
  "${GEN[@]}" --area "$area" --n "$n" > /dev/null
done <<'EOF'
abstract_classes 8
callables 5
constructors_metaclasses 5
context_managers 18
dunder_dispatch 8
final_classvar 5
generics_variance 4
gradual_any 8
inheritance_mro 5
narrowing_user 4
overloads 5
paramspec_concatenate 6
protocols 4
self_classmethods 5
typeddict 6
typevartuple_unpack 3
EOF
"$PY" scripts/inbox_check.py "$WORK/inbox"   # expected: prompts=250 answers=250 answered=250 pending=0 orphan_answers=0
echo "programs written: $(find "$WORK/gen" -name '*.py' | wc -l) (expected 250)"

echo "== 2/3 judge (no LLM, $JOBS jobs)"
TYPEDIFF_LLM=null "$PY" scripts/kbloop_run.py "$WORK/out" "$WORK/gen" --jobs "$JOBS" --pyright-only --progress "$WORK/progress.log"

echo "== 3/3 statistics"
"$PY" scripts/kbloop_stats.py "$WORK/out"
echo "reports: $WORK/out   triage: $PY -m typediff.cli triage $WORK/out --top 20"
