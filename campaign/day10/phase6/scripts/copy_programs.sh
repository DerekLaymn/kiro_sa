#!/bin/bash
# copy the 10 strong-evidence programs verbatim into repro/ as p_<tag>.py
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
P=$K/campaign/day10/phase6
cd $K/runs/day10 || exit 1
while IFS='|' read -r tag pat; do
  src=$(find gen -name "$pat" | head -3)
  n=$(echo "$src" | grep -c .)
  echo "$tag <- $src (matches=$n)"
  first=$(echo "$src" | head -1)
  [ -n "$first" ] && cp "$first" "$P/repro/p_$tag.py"
done <<'EOF'
meta37b4|gen1_37b4e5f8.py
flag_d156|d4v_ty_flag_or_else_never__mut0_d156e44d.py
meta2cca|*constructors_call_metaclass__mut1_2cca6936.py
ovl59ea|*overloads_definitions__mut1_59eaed87.py
eq14fa|s3r1_ty_type_equality_narrowing_any__mut1_14fa674d.py
tvtb167|*paramspec_default_after_tvt__mut0_b16712de.py
abs5c36|gen1_5c366404.py
tvtb077|*paramspec_default_after_tvt__mut1_b0772641.py
pc66a0|*generics_paramspec_components__mut0_66a0b5b8.py
td5eeb|*typedDict10__mut1_5eeeb41b.py
EOF
ls -la $P/repro
