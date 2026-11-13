#!/usr/bin/env bash
# One-command check that a fresh checkout works and gives the reference results. No API key and no LLM are needed.
#
#   python3 -m venv .venv && . .venv/bin/activate
#   pip install -e ".[tools,test]" -c constraints.txt
#   scripts/reproduce.sh
#
# Steps: 1 install and tool versions, 2 test suite, 3 knowledge-base self-test, 4 deterministic judge on the seeds
# (hand-written seeds + the 36 final parent programs, TYPEDIFF_LLM=null), 5 optional replay of the final round.
#
# Environment variables:
#   PYTHON=python3        interpreter (default: python3, else python)
#   SKIP_TESTS=1          skip step 2 (the suite takes about 2-3 minutes)
#   WITH_REPLAY=1         also run scripts/replay_final_round.sh (about 3 minutes, JOBS parallel jobs, at most 6)
#   JOBS=4                parallel jobs of the replay
#   STRICT_PINS=1         stop if an installed tool differs from the pinned version (default: warn and go on)
#   WORK=runs/reproduce   output directory (git-ignored)
#   TYPEDIFF_TOOL_MEM_MB=2048   memory limit per mypy / ty process (default here: 2048; 0 = unlimited; Linux). One seed
#                         program makes mypy use many GB; the limit kills it and records a mypy:signal-SIGKILL crash
#                         finding (as in the reference numbers) without exhausting the machine.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || PY=python
WORK="${WORK:-runs/reproduce}"
TD=("$PY" -m typediff.cli)
export TYPEDIFF_LLM=null   # the judge never needs an LLM; this also ignores a TYPEDIFF_LLM in .env
export TYPEDIFF_TOOL_MEM_MB="${TYPEDIFF_TOOL_MEM_MB:-2048}"

echo "== 1/4 install and tool versions"
"$PY" -c "import typediff" 2>/dev/null || { echo "typediff is not installed: run  pip install -e \".[tools,test]\" -c constraints.txt"; exit 1; }
if [ "${STRICT_PINS:-0}" = 1 ]; then
  "${TD[@]}" --python-version 3.13 doctor --strict
else
  "${TD[@]}" --python-version 3.13 doctor || echo "(continuing: results can differ from the reference)"
fi

if [ "${SKIP_TESTS:-0}" != 1 ]; then
  echo "== 2/4 test suite"
  "$PY" -m pytest -q -p no:cacheprovider
else
  echo "== 2/4 test suite skipped (SKIP_TESTS=1)"
fi

echo "== 3/4 knowledge-base self-test"
mkdir -p "$WORK"
"${TD[@]}" --python-version 3.13 kb-selftest | tee "$WORK/kb-selftest.txt"
kb_pass=$(grep -c '^PASS' "$WORK/kb-selftest.txt" || true)
kb_fail=$(grep -c '^FAIL' "$WORK/kb-selftest.txt" || true)

echo "== 4/4 deterministic judge on the seeds (no LLM)"
SEEDS="$WORK/seeds-in"
rm -rf "$SEEDS" "$WORK/seeds-out"
mkdir -p "$SEEDS"
for d in seeds/*/; do   # everything except the generated, uncommitted seeds/harvested
  [ "$(basename "$d")" = harvested ] || cp -r "$d" "$SEEDS/"
done
"${TD[@]}" --python-version 3.13 --out "$WORK/seeds-out" --no-reduce --audit-rate 0 seeds "$SEEDS" > "$WORK/seeds.txt"
tail -n 1 "$WORK/seeds.txt"
"$PY" - "$WORK/seeds-out" <<'EOF'
import collections, glob, json, sys

tiers, programs, discrepancies = collections.Counter(), 0, 0
for f in sorted(glob.glob(sys.argv[1] + "/*.json")):
    r = json.load(open(f))
    if "findings" not in r:
        continue
    programs += 1
    discrepancies += len(r["discrepancies"])
    tiers.update(x["tier"] for x in r["findings"])
print(f"programs={programs} discrepancies={discrepancies} findings by tier: " + ", ".join(f"{k}={v}" for k, v in sorted(tiers.items())))
EOF

if [ "${WITH_REPLAY:-0}" = 1 ]; then
  echo "== replay of the final round (250 stored answers, no LLM)"
  scripts/replay_final_round.sh "$WORK/replay-final-round"
fi

cat <<EOF

== expected on the pinned versions (mypy 2.4.0, ty 0.0.97, pyright 1.1.414, CPython 3.13)
   tests:        762 passed, no failures (a count above 762 means tests were added since)
   kb-selftest:  PASS=20 FAIL=0              (this run: PASS=$kb_pass FAIL=$kb_fail)
   seeds:        programs=65 discrepancies=88 findings by tier: confirmed=8, dismissed=30, review=60
   replay:       programs=250 discrepancies=247 live=168 dismissed=79 (only with WITH_REPLAY=1; docs/generation.md)
Counts that differ with other tool versions are not a bug in the checkout; see docs/reproducibility.md.
EOF
[ "$kb_fail" = 0 ]
