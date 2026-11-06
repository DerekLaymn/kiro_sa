#!/bin/bash
# copy the 4 reveal_unpaired programs (medium evidence "mypy treats reachable code as unreachable") verbatim into repro3/ as up_<n>.py
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
P=$K/campaign/day10/phase6
mkdir -p $P/repro3
cd $K/runs/day10 || exit 1
for pat in rsv_gradual_any_76921a4b__mut0_ad89194c.py rsv_gradual_any_76921a4b__mut0_00d85d59.py gen3_cbc25173.py gen1_0cecd6f5.py; do
  first=$(find gen -name "*$pat" | grep -E "gradual_any|narrowing_user" | head -1)
  short=$(echo "$pat" | sed 's/rsv_gradual_any_76921a4b__mut0_/ga_/; s/\.py//')
  echo "up_$short <- $first"
  [ -n "$first" ] && cp "$first" "$P/repro3/up_$short.py"
done
