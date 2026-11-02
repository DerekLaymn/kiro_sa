#!/usr/bin/env bash
D=/home/derek/.cache/typediff/docs
echo "#### widen / infer literal"
grep -rIn -i "widen\|infer.*literal\|literal.*infer" $D/spec/literal.txt $D/spec/qualifiers.txt $D/spec/directives.txt 2>/dev/null | head -20
echo "#### assert_type"
grep -rIn -B2 -A12 "assert_type(val" $D/spec/directives.txt | head -50
echo "### mypy docs literal"
grep -rIln "Literal\[" $D/mypy | head
grep -rIn -i "last known\|literal context\|inferred literal\|Literal\[.*\]?" $D/mypy | head -8
