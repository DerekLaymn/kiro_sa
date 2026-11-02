#!/usr/bin/env bash
D=/home/derek/.cache/typediff/docs/mypy
grep -rIn -B4 -A14 "Redefinitions with incompatible types" $D | head -60
echo "#### allow-redefinition-new"
grep -rIn -B2 -A12 "allow-redefinition-new" $D | head -50
echo "#### ty docs: declared type / inferred"
grep -rIn -i "union of all\|inferred type of an undeclared\|undeclared" /home/derek/.cache/typediff/docs/ty | head -10
