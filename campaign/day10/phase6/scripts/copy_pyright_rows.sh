#!/bin/bash
# copy the 10 programs behind the 13 only_pyright runtime_supports rows verbatim into repro3/ as pp_<n>.py
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
P=$K/campaign/day10/phase6
mkdir -p $P/repro3
cd $K/runs/day10 || exit 1
i=0
for pat in gen4_c0f3dbed.py d9p_context_managers_swallowed_name_possibly_unbound__mut2_ecc6e133.py d9p_context_managers_swallowed_name_possibly_unbound__mut1_1d6b71d0.py gen9_44fe19eb.py d5p_descriptors_decorated_get_pyright_rangeerror__mut1_15083425.py d9p_context_managers_swallowed_name_possibly_unbound__mut0_60a08b2b.py d9p_context_managers_swallowed_name_possibly_unbound__mut1_5b3474a9.py d8p_dunder_dispatch_annotation_only_call__mut0_315fa4f3.py gen0_19c44353.py d9p_context_managers_swallowed_name_possibly_unbound__mut2_d57b69f7.py; do
  src=$(find gen -name "*$pat" | head -3)
  n=$(echo "$src" | grep -c .)
  first=$(echo "$src" | head -1)
  short=$(echo "$pat" | sed 's/.*\(mut[0-9]_\)/\1/; s/\.py//; s/d9p_context_managers_swallowed_name_possibly_unbound/cm/' )
  echo "pp_$short <- $first (matches=$n)"
  [ -n "$first" ] && cp "$first" "$P/repro3/pp_$short.py"
done
ls $P/repro3
