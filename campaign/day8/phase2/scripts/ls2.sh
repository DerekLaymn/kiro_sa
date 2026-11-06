#!/usr/bin/env bash
cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa || exit 1
for d in typeddict overloads dataclasses final_classvar match_statement tuples_unpacking self_classmethods; do
  echo "== seeds/$d"; ls seeds/$d
done
echo "== reserve candidates"
for f in overloads/gen7_d41747bd overloads/gen4_7ab4b09b overloads/gen9_d6e90b34 abstract_classes/gen9_ae31b752 \
         tuples_unpacking/tuples_unpacking__variadic_tuples__mut0_b068dfad tuples_unpacking/gen9_c53ea70f \
         dataclasses/dataclasses__overloaded_post_init__mut0_223fff8f recursive_aliases/gen4_0bbabab4 recursive_aliases/gen3_d5395259; do
  ls runs/day7/gen/$f.py
done
echo "== inbox_check usage"; sed -n 1,25p scripts/inbox_check.py
echo "== ops"; grep -n "OPERATORS\|DEPTH_OPS\|CRASH_OPS" typediff/strategy.py | head
