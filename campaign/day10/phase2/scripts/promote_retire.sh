#!/usr/bin/env bash
# Day 10 morning decisions (Plan §3 "Every morning": promote programs with new patterns into runs/hits/, retire
# classified patterns). runs/ is git-ignored; both actions are reversible:
#   rm runs/hits/d9p_context_managers_swallowed_name_possibly_unbound.py
#   mv runs/hits-dropped/<name>.py runs/hits/
# PROMOTED (1): Day-9 program runs/day9/gen/context_managers/gen0_b82d2e9e.py (draft 10, D9-10): a name bound in a `with`
#   whose __exit__ returns bool and used after the block. Reproduces alone (campaign/day10/phase2/results/alone.out, live
#   finding D1 with the same row), highest similarity to any file of runs/hits 0.33 (< 0.80). It is the only program of the
#   area `context_managers`, which has no parent in runs/hits. The copy gets ONE area/hypothesis/origin triple (the Day-9
#   file has two hypothesis lines) and a "Vary:" sentence, as the Day-4 and Day-9 promotions did.
# RETIRED (2), rediscovery-only parents (campaign/day10/phase2/results/parent-live-rows.out, yield-day9-on-day10kb.out):
#   d6p_typevartuple_unpack_pep695_paramspec_default_mypy_subscript: 4 Day-9 mutants, 19 live, 0 strong, 0 dismissed; the live
#     rows are mypy's "Can only replace ParamSpec ..." message (draft 5, filed as mypy#22375) and its consequences
#     (assert-type, reveal `def (*Any, **Any)`, one call-arg), classified by message template.
#   d5p_descriptors_one_decorator_dunders_pyright_rangeerror: 3 Day-9 mutants, 1 live (pyright-only "Object of type .. is not
#     callable", the documented dunder trade-off of D9-9), 0 pyright crash events; its sibling d5p_..decorated_get.. stays as
#     the pyright RangeError reference (draft 7).
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
echo "before: $(ls runs/hits/*.py | wc -l) files in runs/hits, $(ls runs/hits-dropped/*.py | wc -l) in runs/hits-dropped"
SRC=runs/day9/gen/context_managers/gen0_b82d2e9e.py
DST=runs/hits/d9p_context_managers_swallowed_name_possibly_unbound.py
[ -f "$SRC" ] || { echo "promote: missing $SRC" >&2; exit 1; }
if [ -e "$DST" ]; then
  echo "promote: $DST exists, nothing done"
else
  .venv/bin/python - "$SRC" "$DST" <<'PY'
import sys
src, dst = sys.argv[1:3]
lines = open(src).read().split("\n")
body_at = next(i for i, ln in enumerate(lines) if ln.startswith("from "))
body = "\n".join(lines[body_at:])
hyp = ("A with block whose __exit__ returns bool may swallow an exception raised inside the block, so a name bound after the "
       "raising statement is unbound after the block (CPython raises UnboundLocalError); pyright reports the use, ty only "
       "under an off-by-default rule, mypy not even with possibly-undefined. Vary: the __exit__ annotation (None, "
       "Literal[True], Literal[False]), contextlib.suppress, ExitStack, async with, try/finally, del of the name.")
head = ("# area: context_managers\n# hypothesis: " + hyp + "\n"
        "# origin: runs/day9/gen/context_managers/gen0_b82d2e9e.py (Day-9 fresh program, draft 10: mypy does not report a "
        "possibly-undefined name after a swallowing with block)\n")
open(dst, "w").write(head + body)
print("promoted ->", dst)
PY
fi
mkdir -p runs/hits-dropped
for b in d6p_typevartuple_unpack_pep695_paramspec_default_mypy_subscript d5p_descriptors_one_decorator_dunders_pyright_rangeerror; do
  if [ -e "runs/hits/$b.py" ] && [ ! -e "runs/hits-dropped/$b.py" ]; then mv "runs/hits/$b.py" "runs/hits-dropped/$b.py" && echo "retired $b"; else echo "skipped $b"; fi
done
echo "after: $(ls runs/hits/*.py | wc -l) files in runs/hits, $(ls runs/hits-dropped/*.py | wc -l) in runs/hits-dropped"
head -6 "$DST"
.venv/bin/python campaign/day4m/check_hits.py 0.80 > campaign/day10/phase2/results/check_hits-after.out 2>&1
echo "check_hits rc=$?" >> campaign/day10/phase2/results/check_hits-after.out
tail -n 4 campaign/day10/phase2/results/check_hits-after.out
echo "tracked files under runs: $(git ls-files runs | wc -l)"
