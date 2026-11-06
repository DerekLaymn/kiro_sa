#!/bin/bash
# for the 21 non-swallow runtime_supports programs: does pyright's message say it cannot bind the method (missing self)?
K=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
P=$K/campaign/day9/phase6
: > $P/results/pyright_rows.txt
for n in d4v_metaclass_reflected_op__mut1_936af0f7 d8p_dunder_dispatch_annotation_only_call__mut1_ba6a1075 d3p_inheritance_mro_total_ordering_inherited_lt__mut0_73c4aa3f gen8_88778d35 d4v_metaclass_reflected_op__mut0_dcb547ed gen9_8f78c1ef d3p_inheritance_mro_total_ordering_inherited_lt__mut1_19d5c092 constructors_metaclasses__new_returns_other__mut2_d72c127c inheritance_mro__override_lsp__mut0_4842df3b gen3_b4b3cee2 d3p_descriptors_decorated_get__mut1_a8066256 gen14_1e8e47e5 d8p_dunder_dispatch_annotation_only_call__mut2_7fcabe28 inheritance_mro__override_lsp__mut2_efab2ae0 d4v_metaclass_reflected_op__mut2_c5c118f8 d3p_inheritance_mro_total_ordering_inherited_lt__mut2_8f473ccc d5p_descriptors_decorated_get_pyright_rangeerror__mut0_fd790c68 gen21_d547a9e1 d8p_dunder_dispatch_annotation_only_call__mut3_a9c2dc0a constructors_metaclasses__new_returns_other__mut1_824c0d34; do
  f=$(find $K/runs/day9/gen -name "$n.py" | head -1)
  out=$(timeout 120 $K/.venv/bin/pyright --pythonversion 3.13 "$f" 2>&1)
  bind=$(echo "$out" | grep -c "Could not bind method")
  nomember=$(echo "$out" | grep -c -E "Attribute \"__(call|iter|len|getitem|contains)__\" is unknown|is not iterable|No overloads for \"iter\"")
  # does the program declare the dunder annotation-only (class body, no value) or assign it on the instance
  ann=$(grep -c -E "^\s+__[a-z]+__\s*:\s*" "$f")
  inst=$(grep -c -E "self\.__[a-z]+__\s*=" "$f")
  echo "$n bind_msg=$bind other_dunder_msg=$nomember annotation_only_lines=$ann instance_assigned_lines=$inst" >> $P/results/pyright_rows.txt
done
echo finished >> $P/results/pyright_rows.txt
