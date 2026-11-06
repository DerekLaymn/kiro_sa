#!/usr/bin/env bash
# Day 9 morning decision (Plan §3 "Every morning": promote programs with new patterns into runs/hits/).
# Promotes ONE program: the Day-8 mutant d3p_callables_self_call_attr__mut0_5445453a (annotation-only `__call__: Step`,
# CPython raises TypeError, ty and pyright accept `C()()`; day8-report.md section 5, confidence 0.4) as the parent of the
# new area `dunder_dispatch`. The copy gets ONE area/hypothesis/origin triple (the Day-8 file carries two) and a
# "Vary:" sentence, as the Day-4 promotions did (campaign/day4m/mk_parents.py). runs/ is git-ignored; reversible by `rm`.
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
SRC=runs/day8/gen/callables/d3p_callables_self_call_attr__mut0_5445453a.py
DST=runs/hits/d8p_dunder_dispatch_annotation_only_call.py
[ -f "$SRC" ] || { echo "promote: missing $SRC" >&2; exit 1; }
[ ! -e "$DST" ] || { echo "promote: $DST exists, nothing done"; exit 0; }
.venv/bin/python - "$SRC" "$DST" <<'PY'
import sys
src, dst = sys.argv[1:3]
lines = open(src).read().split("\n")
body_at = next(i for i, ln in enumerate(lines) if ln.startswith("from "))
body = "\n".join(lines[body_at:])
hyp = ("A class whose __call__ exists only as an annotation (`__call__: Step`, no definition) must be rejected when an "
       "instance is called, and CPython raises TypeError because special methods are looked up on the type, so a checker "
       "that accepts `C()()` is unsound. Vary: the protocol (iter, len, getitem, enter, contains), an instance "
       "assignment `self.__call__ = fn`, a metaclass-level definition, an inherited definition as control.")
head = ("# area: dunder_dispatch\n# hypothesis: " + hyp + "\n"
        "# origin: runs/day8/gen/callables/d3p_callables_self_call_attr__mut0_5445453a.py (Day-8 mutant of "
        "d3p_callables_self_call_attr; ty and pyright accept the call, mypy rejects it for another reason)\n")
open(dst, "w").write(head + body)
print("promoted ->", dst)
PY
head -8 "$DST"
