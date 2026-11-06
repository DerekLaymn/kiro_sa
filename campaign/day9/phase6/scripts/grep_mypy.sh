#!/bin/bash
F=$(find /tmp/d3v-master -name checkexpr.py -path '*mypy*' 2>/dev/null | head -1)
echo "$F"
grep -n "op_methods_that_shortcut\|lookup_definer\|is_same_type(left_type, right_type)" "$F" | head -20
echo ----
grep -n "op_methods_that_shortcut" -A8 "$(dirname "$F")/operators.py" | head -30
echo ---- block
N=$(grep -n "op_methods_that_shortcut and is_same_type" "$F" | head -1 | cut -d: -f1)
sed -n "$((N-12)),$((N+40))p" "$F"
