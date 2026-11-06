#!/usr/bin/env bash
# Day 8 phase 5 (Plan §3 "Every morning: promote parents", triage checklist 1 "reproduce alone"): every program of
# runs/day8/gen with a live finding with strong bug evidence is re-run ALONE (own input dir, --jobs 1, --pyright-only),
# then its similarity to every file of runs/hits is computed (same body() and difflib ratio as campaign/day4m/check_hits.py).
# Read-only on runs/hits. Output: alone.out (rc, stats line, discrepancy rows, strong evidence rows per candidate).
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
cd "$ROOT" || exit 1
export TYPEDIFF_LLM=null
W=/tmp/d8p5/alone
rm -rf "$W"; mkdir -p "$W"
i=0
while read -r f; do
  i=$((i+1))
  mkdir -p "$W/in$i"
  cp "runs/day8/gen/$f" "$W/in$i/"
  .venv/bin/python scripts/kbloop_run.py "$W/out$i" "$W/in$i" --jobs 1 --pyright-only --progress "$W/prog$i.log" > "$W/run$i.log" 2>&1
  echo "== $i $f rc=$?"
  .venv/bin/python scripts/kbloop_stats.py "$W/out$i" 2>&1 | head -1
  grep -h -E "^\| D|^\| C" "$W"/out$i/seed-*.md
  grep -h -E "strong/verified, supports bug|STACKTRACE" "$W"/out$i/seed-*.md | cut -c1-220
done <<'EOF'
tuples_unpacking/d7p_tuples_unpacking_partial_unpack_except_ty__mut0_cdecbcd7.py
tuples_unpacking/d7p_tuples_unpacking_partial_unpack_except_ty__mut0_aa1f1387.py
tuples_unpacking/d7p_tuples_unpacking_partial_unpack_except_ty__mut0_d873ebcb.py
tuples_unpacking/d7p_tuples_unpacking_partial_unpack_except_ty__mut1_cfdf17ba.py
descriptors_properties/d4p_descriptors_readonly_prop_never__mut0_f116e46b.py
descriptors_properties/d4p_descriptors_readonly_prop_never__mut1_17c399aa.py
descriptors_properties/d3p_descriptors_decorated_get__mut0_655e135a.py
overloads/rsv_overloads_d41747bd__mut0_1de657a6.py
overloads/rsv_overloads_d41747bd__mut0_f7c04c87.py
overloads/gen12_a368580c.py
self_classmethods/self_classmethods__self_param_inherited__mut0_3a63c673.py
EOF
echo "== similarity"
.venv/bin/python campaign/day8/phase5/similarity.py
